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
        return get_active_tasks_for_user(user=self.user, id=self.task_id).exists()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)
        self.close()

    def frame_discard_other_connections(self, event):
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)
        self.close()

    def receive(self, text_data=None, bytes_data=None):
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
                    'date_frame_id': str(new_date_frame.id),
                    'frame_type': new_date_frame.get_frame_type_display()
                }
            }))

    def frame_finish(self, event):
        current_date_frame_id = self.scope['date_frame_id']
        finish_date_frame(date_frame_id=current_date_frame_id)

        self.send(text_data=json.dumps({
            'level': statuses.MESSAGE_LEVEL_CHOICES[statuses.LEVEL_TYPE_SUCCESS],
            'code': statuses.LEVEL_TYPE_SUCCESS,
            'action': statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_FINISHED],
            'data': {
                'date_frame_id': str(current_date_frame_id.id),
                'frame_type': current_date_frame_id.get_frame_type_display()
            }
        }))

    def frame_terminate(self, event):
        finished_date_frame = force_finish_date_frame(task_id=self.task_id, notify=False)
        if finished_date_frame:
            self.notify_frame_terminated()

    def frame_notify_frame_terminated(self, event):
        self.notify_frame_terminated()

    def notify_frame_terminated(self):
        self.send(text_data=json.dumps({
            'level': statuses.MESSAGE_LEVEL_CHOICES[statuses.LEVEL_TYPE_WARNING],
            'code': statuses.LEVEL_TYPE_WARNING,
            'action': statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_FORCE_TERMINATED],
        }))
