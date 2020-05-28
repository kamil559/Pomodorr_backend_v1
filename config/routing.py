from channels.routing import ProtocolTypeRouter

from pomodorr.auth.middlewares import JsonTokenAuthMiddlewareStack
from pomodorr.frames.routing import websocket_urls

application = ProtocolTypeRouter({
    'websocket': JsonTokenAuthMiddlewareStack(websocket_urls)
})
