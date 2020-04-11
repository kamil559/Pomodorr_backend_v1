import pytest

from pomodorr.auth.auth_serializers import CustomJSONWebTokenSerializer, CustomVerificationBaseSerializer
from pomodorr.tools.utils import get_time_delta

pytestmark = pytest.mark.django_db


def test_jwt_serializer_valid_credentials(user_data, active_user):
    serializer = CustomJSONWebTokenSerializer(data={
        'email': user_data.get('email'),
        'password': user_data.get('password')
    })

    assert serializer.is_valid()


def test_jwt_serializer_inactive_user(non_active_user_data, non_active_user):
    serializer = CustomJSONWebTokenSerializer(data={
        'email': non_active_user_data.get('email'),
        'password': non_active_user_data.get('password')
    })

    assert serializer.is_valid() is False
    assert serializer.errors['non_field_errors'][0] == 'Unable to log in with provided credentials.'


def test_jwt_serializer_blocked_user(blocked_user_data, blocked_user):
    serializer = CustomJSONWebTokenSerializer(data={
        'email': blocked_user_data.get('email'),
        'password': blocked_user_data.get('password')
    })

    assert serializer.is_valid() is False
    assert serializer.errors['non_field_errors'][
               0] == 'Your account is currently blocked. For further details contact the administration.'


def test_jwt_verify_serializer_invalid_token(json_web_token):
    serializer = CustomVerificationBaseSerializer(data={
        'token': json_web_token + 'xyz'
    })

    assert serializer.is_valid() is False
    assert serializer.errors['non_field_errors'][0] == 'Error decoding signature.'


def test_jwt_verify_serializer_inactive_user(json_web_token, active_user):
    active_user.is_active = False
    active_user.save()

    serializer = CustomVerificationBaseSerializer(data={
        'token': json_web_token
    })

    assert serializer.is_valid() is False
    assert serializer.errors['non_field_errors'][0] == 'User account is disabled.'


def test_jwt_verify_serializer_blocked_user(json_web_token, active_user):
    active_user.blocked_until = get_time_delta({"days": 1})
    active_user.save()

    serializer = CustomVerificationBaseSerializer(data={
        'token': json_web_token
    })

    assert serializer.is_valid() is False
    assert serializer.errors['non_field_errors'][
               0] == 'Your account is currently blocked. For further details contact the administration.'
