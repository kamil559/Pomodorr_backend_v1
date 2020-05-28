import json

from channels.exceptions import DenyConnection
from channels.generic.websocket import WebsocketConsumer


class DateFrameConsumer(WebsocketConsumer):
    def connect(self):
        user = self.scope['user']

        if not user.is_authenticated:
            raise DenyConnection

        self.accept()

    def disconnect(self, code):
        pass

    def receive(self, text_data=None, bytes_data=None):
        print(text_data)

        self.send(text_data=json.dumps({
            'message': text_data
        }))
