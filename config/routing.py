from channels.routing import ProtocolTypeRouter
from channels.security.websocket import AllowedHostsOriginValidator

from pomodorr.auth.middlewares import JsonTokenAuthMiddlewareStack
from pomodorr.frames.routing import frames_application

application = ProtocolTypeRouter({
    'websocket': AllowedHostsOriginValidator(
        JsonTokenAuthMiddlewareStack(frames_application)
    )
})
