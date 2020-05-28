from http import cookies

from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections

from pomodorr.auth.auth_classes import CustomJWTWebTokenAuthentication


class JsonWebTokenAuthenticationFromScope(CustomJWTWebTokenAuthentication):
    """
    Extracts the JWT from a channel scope (instead of an http request)
    """

    def get_jwt_value(self, scope):
        try:
            cookie = next(x for x in scope['headers'] if x[0].decode('utf-8') == 'cookie')[1].decode('utf-8')
            return cookies.SimpleCookie(cookie)['JWT'].value
        except:
            return None

    # async def authenticate(self, request):
    #     return await super(JsonWebTokenAuthenticationFromScope, self).authenticate(request)


class JsonTokenAuthMiddlewareInstance(CustomJWTWebTokenAuthentication):
    """
    Token authorization middleware for Django Channels 2
    """

    def __init__(self, scope, middleware):
        self.scope = scope
        self.middleware = middleware
        self.inner = self.middleware.inner

    async def __call__(self, receive, send):
        try:
            # Close old database connections to prevent usage of timed out connections
            await database_sync_to_async(close_old_connections)()

            self.scope['user'], jwt_value = await database_sync_to_async(
                JsonWebTokenAuthenticationFromScope().authenticate)(self.scope)
        except Exception as e:
            self.scope['user'] = AnonymousUser()

        inner = self.inner(self.scope)
        return await inner(receive, send)


class JsonTokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        return JsonTokenAuthMiddlewareInstance(scope, self)


JsonTokenAuthMiddlewareStack = lambda inner: JsonTokenAuthMiddleware(AuthMiddlewareStack(inner))
