from channels.routing import URLRouter
from django.urls import path

from pomodorr.frames.consumers import DateFrameConsumer

frames_application = URLRouter([
    path('date_frames/<uuid:task_id>/', DateFrameConsumer)
])
