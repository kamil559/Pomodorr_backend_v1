import pytest
from django.utils import timezone

from pomodorr.users.selectors import (get_all_users, get_active_standard_users, get_non_active_standard_users,
                                      get_blocked_standard_users, get_ready_to_unblock_users)

pytestmark = pytest.mark.django_db


def test_get_all_users(user_model, active_user, non_active_user):
    service_method_result = get_all_users()
    orm_query_result = user_model.objects.all()

    assert service_method_result.count() == orm_query_result.count()
    assert list(service_method_result) == list(orm_query_result)


def test_get_active_standard_users(user_model, active_user, non_active_user, admin_user):
    service_method_results = get_active_standard_users()
    orm_query_result = user_model.objects.filter(
        is_active=True,
        blocked_until__isnull=True,
        is_superuser=False,
        is_staff=False
    )

    assert service_method_results.count() == orm_query_result.count()
    assert list(service_method_results) == list(orm_query_result)


def test_get_non_active_standard_users(user_model, active_user, non_active_user, admin_user):
    service_method_result = get_non_active_standard_users()
    orm_query_result = user_model.objects.filter(
        is_active=False,
        blocked_until__isnull=True,
        is_superuser=False,
        is_staff=False
    )

    assert service_method_result.count() == orm_query_result.count()
    assert list(service_method_result) == list(orm_query_result)


def test_get_blocked_standard_users(user_model, active_user, non_active_user, admin_user, blocked_user):
    service_method_result = get_blocked_standard_users()
    orm_query_result = user_model.objects.filter(
        blocked_until__isnull=False,
        is_superuser=False,
        is_staff=False
    )

    assert service_method_result.count() == orm_query_result.count()
    assert list(service_method_result) == list(orm_query_result)
    assert all(user.is_blocked for user in service_method_result)


def test_get_ready_to_unblock_users(user_model, active_user, non_active_user, admin_user, blocked_user,
                                    ready_to_unblock_user):
    service_method_result = get_ready_to_unblock_users()
    orm_query_result = user_model.objects.filter(
        blocked_until__isnull=False,
        blocked_until__lt=timezone.now()
    )

    assert service_method_result.count() == orm_query_result.count()
    assert list(service_method_result) == list(orm_query_result)
    assert all(user.is_blocked for user in service_method_result)
