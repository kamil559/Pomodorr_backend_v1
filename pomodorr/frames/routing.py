from channels.routing import URLRouter
from django.urls import path

from pomodorr.frames.consumers import DateFrameConsumer

websocket_urls = URLRouter([
    path('date_frames/<uuid:date_frames_id>/', DateFrameConsumer)
])
