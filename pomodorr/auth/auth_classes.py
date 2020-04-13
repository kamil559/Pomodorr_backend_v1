from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _
from rest_framework import exceptions
from rest_framework_jwt.authentication import BaseJSONWebTokenAuthentication, JSONWebTokenAuthentication

from rest_framework_jwt.settings import api_settings


jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
jwt_get_username_from_payload = api_settings.JWT_PAYLOAD_GET_USERNAME_HANDLER


class CustomJWTWebTokenAuthentication(BaseJSONWebTokenAuthentication):
    def authenticate_credentials(self, payload):
        """
        Returns an user that matches the payload's user id and email unless it is not active or blocked.
        """
        User = get_user_model()
        username = jwt_get_username_from_payload(payload)

        if not username:
            msg = _('Invalid payload.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            user = User.objects.get_by_natural_key(username)
        except User.DoesNotExist:
            msg = _('Invalid signature.')
            raise exceptions.AuthenticationFailed(msg)
        else:
            if not user.is_active:
                msg = _('User account is disabled.')
                raise exceptions.AuthenticationFailed(msg)

            if user.is_blocked:
                msg = _('User account is currently blocked.')
                raise exceptions.AuthenticationFailed(msg)

        return user


class CustomJSONWebTokenAuthentication(CustomJWTWebTokenAuthentication, JSONWebTokenAuthentication):
    pass
