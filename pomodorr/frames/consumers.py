import json
from collections import Mapping
from json import JSONDecodeError

from asgiref.sync import async_to_sync
from channels.exceptions import DenyConnection
from channels.generic.websocket import WebsocketConsumer
from django.core.exceptions import ValidationError

from pomodorr.frames import statuses
from pomodorr.frames.exceptions import DateFrameException
from pomodorr.frames.models import DateFrame
from pomodorr.frames.services.date_frame_service import start_date_frame, finish_date_frame, force_finish_date_frame
from pomodorr.projects.selectors.task_selector import get_active_tasks_for_user


class DateFrameConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super(DateFrameConsumer, self).__init__(*args, **kwargs)
        self.user = self.scope['user']
        self.task_id = str(self.scope['url_route']['kwargs']['task_id'])
        self.group_name = f'task_{self.task_id}'

        self.user_available_handlers_mapping = {
            'frame_start': 'frame.start',
            'frame_finish': 'frame.finish',
            'frame_terminate': 'frame.terminate'
        }

    def connect(self):
        """
        In the first step this method authorizes the user trying to connect to the socket.
        Then if there is any ongoing date frame for the task which the connection points to, it will be terminated and
        the connection that corresponds to the ongoing date frame is about to be discarded.
        This means that there can be only one connection responsible for calculating the date frames per the task.
        Then the connection is being accepted.
        """
        if not self.user.is_authenticated or not self.has_object_permission():
            raise DenyConnection

        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'frame.terminate',
            }
        )

        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'frame.discard_other_connections',
            }
        )

        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()

    def has_object_permission(self) -> bool:
        """
        | Checks if the task that the connection corresponds to belongs to the socket user.

        :return: bool
        """
        return get_active_tasks_for_user(user=self.user, id=self.task_id).exists()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)
        self.close()

    def frame_discard_other_connections(self, event):
        """
        Called in order to discard the connection and remove it from the channel group.
        """
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)
        self.close()

    def receive(self, text_data=None, bytes_data=None):
        """
        Receives the text_data, parses it and delegates the further flow to the relevant handler.
        Possible handlers:

            - frame_start
            - frame_finish
            - frame_terminate

        Example json parameters:

            - 'type': 'frame_start',
            - 'frame_type': 0
        """
        try:
            text_data = json.loads(text_data)
            handler = text_data.get('type') if isinstance(text_data, Mapping) else None
        except KeyError:
            self.send(text_data=json.dumps({
                'level': statuses.MESSAGE_LEVEL_CHOICES[statuses.LEVEL_TYPE_ERROR],
                'code': statuses.LEVEL_TYPE_ERROR,
                'action': statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_ABORTED],
                'errors': {
                    'non_field_errors': [statuses.ERROR_MESSAGES[statuses.ERROR_INCOMPLETE_DATA]]
                }
            }))
        except JSONDecodeError:
            self.send(text_data=json.dumps({
                'level': statuses.MESSAGE_LEVEL_CHOICES[statuses.LEVEL_TYPE_ERROR],
                'code': statuses.LEVEL_TYPE_ERROR,
                'action': statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_ABORTED],
                'errors': {
                    'non_field_errors': [statuses.ERROR_MESSAGES[statuses.ERROR_INVALID_DATA_TYPE]]
                }
            }))
        else:
            if handler and handler in self.user_available_handlers_mapping:
                try:
                    async_to_sync(self.channel_layer.group_send)(
                        self.group_name,
                        {
                            'type': self.user_available_handlers_mapping[handler],
                            'content': text_data
                        }
                    )
                except DateFrame.DoesNotExist:
                    self.send(text_data=json.dumps({
                        'level': statuses.MESSAGE_LEVEL_CHOICES[statuses.LEVEL_TYPE_ERROR],
                        'code': statuses.LEVEL_TYPE_ERROR,
                        'action': statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_ABORTED],
                        'errors': {
                            'id': [DateFrameException.messages[DateFrameException.does_not_exist]]
                        }
                    }))
                except ValidationError as exception:
                    self.send(text_data=json.dumps({
                        'level': statuses.MESSAGE_LEVEL_CHOICES[statuses.LEVEL_TYPE_ERROR],
                        'code': statuses.LEVEL_TYPE_ERROR,
                        'action': statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_ABORTED],
                        'errors': exception.message_dict if exception.message_dict is not None else exception.messages
                    }))
            else:
                self.send(text_data=json.dumps({
                    'level': statuses.MESSAGE_LEVEL_CHOICES[statuses.LEVEL_TYPE_ERROR],
                    'code': statuses.LEVEL_TYPE_ERROR,
                    'action': statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_ABORTED],
                    'errors': {
                        'non_field_errors': [statuses.ERROR_MESSAGES[statuses.ERROR_INVALID_HANDLER]]
                    }
                }))

    def frame_start(self, event):
        """
        Called in order to start a date frame. If there are any colliding date frames, they will be
        finished immediately.
        In order to call the handler, the following data is expected by the main receive handler:

            - type: str pointing to frame_start handler,
            - frame_type: int corresponding to the date frame types:

        Valid frame_type values:

            - 0 corresponds to pomodoro
            - 1 corresponds to break
            - 2 corresponds to pause
        """

        try:
            frame_type = event['content']['frame_type']
        except KeyError:
            self.send(text_data=json.dumps({
                'level': statuses.MESSAGE_LEVEL_CHOICES[statuses.LEVEL_TYPE_ERROR],
                'code': statuses.LEVEL_TYPE_ERROR,
                'action': statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_ABORTED],
                'errors': {
                    'non_field_errors': [statuses.ERROR_MESSAGES[statuses.ERROR_INCOMPLETE_DATA]]
                }
            }))
        else:
            new_date_frame = start_date_frame(task_id=self.task_id, frame_type=frame_type)

            self.send(text_data=json.dumps({
                'level': statuses.MESSAGE_LEVEL_CHOICES[statuses.LEVEL_TYPE_SUCCESS],
                'code': statuses.LEVEL_TYPE_SUCCESS,
                'action': statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_STARTED],
                'data': {
                    'date_frame_id': str(new_date_frame.id)
                }
            }))

    def frame_finish(self, event):
        """
        Called in order to finish a date frame. If there are any colliding date frames, they will be
        finished immediately.
        In order to call the handler, the following data is expected by the main receive handler:

            - type: str pointing to frame_start handler,
            - date_frame_id: int corresponding to the date frame that was currently being processed

        Valid frame_type values:

            - 0 corresponds to pomodoro
            - 1 corresponds to break
            - 2 corresponds to pause
        """
        try:
            current_date_frame_id = event['content']['date_frame_id']
        except KeyError:
            self.send(text_data=json.dumps({
                'level': statuses.MESSAGE_LEVEL_CHOICES[statuses.LEVEL_TYPE_ERROR],
                'code': statuses.LEVEL_TYPE_ERROR,
                'action': statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_ABORTED],
                'errors': {
                    'non_field_errors': [statuses.ERROR_MESSAGES[statuses.ERROR_INCOMPLETE_DATA]]
                }
            }))
        else:
            finish_date_frame(date_frame_id=current_date_frame_id)

            self.send(text_data=json.dumps({
                'level': statuses.MESSAGE_LEVEL_CHOICES[statuses.LEVEL_TYPE_SUCCESS],
                'code': statuses.LEVEL_TYPE_SUCCESS,
                'action': statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_FINISHED],
                'data': {
                    'date_frame_id': current_date_frame_id
                }
            }))

    def frame_terminate(self, event):
        """
        Called in order to fetch the ongoing date frame for the task that the connection corresponds to and if there
        is one, it will be terminated. This handler is called before establishing each connection.
        """
        finished_date_frame = force_finish_date_frame(task_id=self.task_id, notify=False)
        if finished_date_frame:
            self.notify_frame_terminated()

    def frame_notify_frame_terminated(self, event):
        """
        Called in order to notify the connected user that the currently processed date frame has been
        terminated. This happens if someone had started another date frame for the related task from another device
        or browser and in case when there is a date frame being processed and in the meantime the related task has been
        marked as completed, which will trigger the signal handler.
        """
        self.notify_frame_terminated()

    def notify_frame_terminated(self):
        """
        Called in order to send the info about the event of terminating the date frame.
        """
        self.send(text_data=json.dumps({
            'level': statuses.MESSAGE_LEVEL_CHOICES[statuses.LEVEL_TYPE_WARNING],
            'code': statuses.LEVEL_TYPE_WARNING,
            'action': statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_FORCE_TERMINATED],
        }))
