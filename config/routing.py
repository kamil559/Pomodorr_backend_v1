from channels.routing import ProtocolTypeRouter

from pomodorr.auth.middlewares import JsonTokenAuthMiddlewareStack
from pomodorr.frames.routing import frames_application

application = ProtocolTypeRouter({
    'websocket': JsonTokenAuthMiddlewareStack(frames_application)
})
