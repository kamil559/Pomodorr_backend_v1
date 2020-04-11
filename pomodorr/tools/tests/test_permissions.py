from unittest.mock import Mock

import pytest
from django.contrib.auth.models import AnonymousUser

from pomodorr.tools.permissions import IsObjectOwner, IsNotAuthenticated

pytestmark = pytest.mark.django_db


def test_is_object_owner_successfully(active_user):
    mock_request = Mock()
    mock_obj = Mock()
    mock_view = Mock()

    mock_request.user = active_user
    mock_obj.user = active_user

    is_object_owner_permission = IsObjectOwner()
    check_permission = is_object_owner_permission.has_object_permission(
        request=mock_request,
        view=mock_view,
        obj=mock_obj
    )

    assert check_permission is True


def test_is_object_owner_with_different_user(active_user):
    mock_request = Mock()
    mock_obj = Mock()
    mock_view = Mock()
    obj_owner = Mock()

    mock_request.user = active_user
    mock_obj.user = obj_owner

    is_object_owner_permission = IsObjectOwner()
    check_permission = is_object_owner_permission.has_object_permission(
        request=mock_request,
        view=mock_view,
        obj=mock_obj
    )

    assert check_permission is False


def test_is_not_authenticated_with_unauthenticated_user():
    mock_request = Mock()
    mock_view = Mock()
    mock_request.user = AnonymousUser()

    is_not_authenticated_permission = IsNotAuthenticated()

    check_permission = is_not_authenticated_permission.has_permission(
        request=mock_request,
        view=mock_view
    )

    assert check_permission is True


def test_is_not_authenticated_with_authenticated_user():
    mock_request = Mock()
    mock_view = Mock()
    mock_user = Mock()
    mock_user.is_authenticated = True
    mock_request.user = mock_user

    is_not_authenticated_permission = IsNotAuthenticated()

    check_permission = is_not_authenticated_permission.has_permission(
        request=mock_request,
        view=mock_view
    )

    assert check_permission is False
