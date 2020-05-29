import json
from collections import Mapping

from asgiref.sync import async_to_sync
from channels.exceptions import DenyConnection
from channels.generic.websocket import WebsocketConsumer

from pomodorr.frames import statuses


class DateFrameConsumer(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super(DateFrameConsumer, self).__init__(*args, **kwargs)
        self.user = self.scope['user']
        self.group_name = str(self.scope['url_route']['kwargs']['date_frames_id'])

        self.available_handlers_mapping = {
            'frame_started': 'frame.started',
            'frame_paused': 'frame.paused',
            'frame_resumed': 'frame.resumed',
            'frame_completed': 'frame.completed',
            'frame_terminated': 'frame.terminated',
            'frame_force_terminate': 'frame.force_terminated'
        }

    def connect(self):
        if not self.user.is_authenticated:
            raise DenyConnection
        else:
            self.accept()

        self.force_terminate_current_task_frames()
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)
        self.close()

    def receive(self, text_data=None, bytes_data=None):
        handler = text_data.get('type') if isinstance(text_data, Mapping) else None

        if handler and handler in self.available_handlers_mapping:
            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    'type': self.available_handlers_mapping[handler],
                    'text': text_data
                }
            )

    def force_terminate_current_task_frames(self):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                "type": "frame.force_terminated",
                "level": statuses.MESSAGE_LEVEL_CHOICES[statuses.LEVEL_TYPE_WARNING],
                "content": statuses.MESSAGE_FRAME_ACTION_CHOICES[statuses.FRAME_ACTION_FORCE_TERMINATED]
            }
        )

    def frame_started(self, event):
        pass

    def frame_paused(self, event):
        pass

    def frame_resumed(self, event):
        pass

    def frame_completed(self, event):
        pass

    def frame_terminated(self, event):
        pass

    def frame_force_terminated(self, event):
        self.send(text_data=json.dumps(event))
