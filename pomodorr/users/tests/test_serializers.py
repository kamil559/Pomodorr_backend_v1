import pytest

from pomodorr.users.serializers import UserDetailSerializer
from pomodorr.users.tests.factories import prepare_file_bytes_to_upload

pytestmark = pytest.mark.django_db


def test_user_detail_serializer(user_data, active_user):
    serializer = UserDetailSerializer(instance=active_user)

    assert serializer.data.get("id") == str(active_user.id)
    assert serializer.data.get("email") == user_data.get("email")
    assert serializer.data.get("username") == user_data.get("username")
    assert serializer.data.get("avatar") is None


def test_user_detail_serializer_with_valid_avatar(user_data, active_user):
    user_data["avatar"] = prepare_file_bytes_to_upload()

    serializer = UserDetailSerializer(instance=active_user, data=user_data)

    assert serializer.is_valid()


def test_user_detail_serializer_with_invalid_avatar_extension(user_data, active_user):
    user_data["avatar"] = prepare_file_bytes_to_upload(name='test.gif', ext='gif')

    serializer = UserDetailSerializer(instance=active_user, data=user_data)

    assert serializer.is_valid() is not True
    assert serializer.errors["avatar"] is not None
