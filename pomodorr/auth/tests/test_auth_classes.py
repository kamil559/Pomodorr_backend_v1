import pytest
from rest_framework.exceptions import AuthenticationFailed

from pomodorr.auth.auth_classes import CustomJWTWebTokenAuthentication, jwt_decode_handler
from pomodorr.tools.utils import get_time_delta

pytestmark = pytest.mark.django_db


def test_authentication_succeeds_for_active_user(json_web_token, active_user):
    payload = jwt_decode_handler(json_web_token)

    jwt_authentication_class = CustomJWTWebTokenAuthentication()

    authentication_result = jwt_authentication_class.authenticate_credentials(payload=payload)

    assert authentication_result == active_user


def test_authentication_fails_for_blocked_user(json_web_token, active_user):
    active_user.blocked_until = get_time_delta({"days": 1})
    active_user.save()
    payload = jwt_decode_handler(json_web_token)

    jwt_authentication_class = CustomJWTWebTokenAuthentication()

    with pytest.raises(AuthenticationFailed) as exc:
        jwt_authentication_class.authenticate_credentials(payload=payload)

    assert exc.value.args[0] == 'Your account is currently blocked. For further details contact the administration.'
