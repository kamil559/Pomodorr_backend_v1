import json
from collections import Mapping

from asgiref.sync import async_to_sync
from channels.exceptions import DenyConnection
from channels.generic.websocket import WebsocketConsumer
from django.core.exceptions import ValidationError

from pomodorr.frames import statuses
from pomodorr.frames.exceptions import DateFrameException
from pomodorr.frames.models import DateFrame
from pomodorr.frames.services.date_frame_service import start_date_frame, finish_date_frame, force_finish_date_frame


class DateFrameConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super(DateFrameConsumer, self).__init__(*args, **kwargs)
        self.user = self.scope['user']
        self.task_id = str(self.scope['url_route']['kwargs']['task_id'])
        self.group_name = f'task_{self.task_id}'

        self.user_available_handlers_mapping = {
            'frame_start': 'frame.start',
            'frame_finish': 'frame.finish',
            'frame_terminated': 'frame.terminated'
        }

    def connect(self):
        if not self.user.is_authenticated:
            raise DenyConnection
        self.accept()

        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'frame.terminated',
            }
        )

        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)
        self.close()

    def receive(self, text_data=None, bytes_data=None):
        handler = text_data.get('type') if isinstance(text_data, Mapping) else None

        if handler and handler in self.user_available_handlers_mapping:
            try:
                async_to_sync(self.channel_layer.group_send)(
                    self.group_name,
                    {
                        'type': self.user_available_handlers_mapping[handler],
                        'content': text_data
                    }
                )
            except KeyError:
                self.send(text_data=json.dumps({
                    'level': statuses.LEVEL_TYPE_ERROR,
                    'code': statuses.FRAME_ACTION_ABORTED,
                    'action': statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_ABORTED],
                    'errors': {
                        'non_field_errors': [statuses.ERROR_MESSAGES[statuses.ERROR_INCOMPLETE_DATA]]
                    }
                }))
            except DateFrame.DoesNotExist:
                self.send(text_data=json.dumps({
                    'level': statuses.LEVEL_TYPE_ERROR,
                    'code': statuses.FRAME_ACTION_ABORTED,
                    'action': statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_ABORTED],
                    'errors': {
                        'id': [DateFrameException.messages[DateFrameException.does_not_exist]]
                    }
                }))
            except ValidationError as exception:
                self.send(text_data=json.dumps({
                    'level': statuses.LEVEL_TYPE_ERROR,
                    'code': statuses.FRAME_ACTION_ABORTED,
                    'action': statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_ABORTED],
                    'errors': exception.message_dict if exception.message_dict is not None else exception.messages
                }))
        else:
            self.send(text_data=json.dumps({
                'level': statuses.LEVEL_TYPE_ERROR,
                'code': statuses.FRAME_ACTION_ABORTED,
                'action': statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_ABORTED],
                'errors': {
                    'non_field_errors': [statuses.ERROR_MESSAGES[statuses.ERROR_INVALID_HANDLER]]
                }
            }))

    def frame_start(self, event):
        frame_type = event['content']['frame_type']
        new_date_frame = start_date_frame(task_id=self.task_id, frame_type=frame_type)

        self.send(text_data=json.dumps({
            'level': statuses.LEVEL_TYPE_SUCCESS,
            'code': statuses.FRAME_ACTION_STARTED,
            'action': statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_STARTED],
            'data': {
                'date_frame_id': new_date_frame.id,
                'frame_type': new_date_frame.get_frame_type_display()
            }
        }))

    def frame_finish(self, event):
        current_date_frame_id = self.scope['date_frame_id']
        finish_date_frame(date_frame_id=current_date_frame_id)

        self.send(text_data=json.dumps({
            'level': statuses.LEVEL_TYPE_SUCCESS,
            'code': statuses.FRAME_ACTION_FINISHED,
            'action': statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_FINISHED],
            'data': {
                'date_frame_id': current_date_frame_id.id,
                'frame_type': current_date_frame_id.get_frame_type_display()
            }
        }))

    def frame_terminated(self, event):
        finished_date_frame = force_finish_date_frame(task_id=self.task_id)

        if finished_date_frame is None:
            self.send(text_data=json.dumps({
                'level': statuses.MESSAGE_LEVEL_CHOICES[statuses.LEVEL_TYPE_NEUTRAL],
                'code': statuses.FRAME_NO_ACTION_TAKEN,
                'action': statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_NO_ACTION_TAKEN],
                'data': {}
            }))
        else:
            self.send(text_data=json.dumps({
                'level': statuses.MESSAGE_LEVEL_CHOICES[statuses.LEVEL_TYPE_WARNING],
                'code': statuses.FRAME_ACTION_FORCE_TERMINATED,
                'action': statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_FORCE_TERMINATED],
                'data': {
                    'date_frame_id': finished_date_frame.id,
                    'frame_type': finished_date_frame.get_frame_type_display()
                }
            }))
