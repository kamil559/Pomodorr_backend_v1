import pytest
from django.utils import timezone

from pomodorr.users.services import UserDomainModel

pytestmark = pytest.mark.django_db


def test_get_all_users(user_model, active_user, non_active_user):
    service_method_result = UserDomainModel.get_all_users()
    orm_query_result = user_model.objects.all()

    assert service_method_result.count() == orm_query_result.count()
    assert list(service_method_result) == list(orm_query_result)


def test_get_active_standard_users(user_model, active_user, non_active_user, admin_user):
    service_method_results = UserDomainModel.get_active_standard_users()
    orm_query_result = user_model.objects.filter(
        is_active=True,
        blocked_until__isnull=True,
        is_superuser=False,
        is_staff=False
    )

    assert service_method_results.count() == orm_query_result.count()
    assert list(service_method_results) == list(orm_query_result)


def test_get_non_active_standard_users(user_model, active_user, non_active_user, admin_user):
    service_method_result = UserDomainModel.get_non_active_standard_users()
    orm_query_result = user_model.objects.filter(
        is_active=False,
        blocked_until__isnull=True,
        is_superuser=False,
        is_staff=False
    )

    assert service_method_result.count() == orm_query_result.count()
    assert list(service_method_result) == list(orm_query_result)


def test_get_blocked_standard_users(user_model, active_user, non_active_user, admin_user, blocked_user):
    service_method_result = UserDomainModel.get_blocked_standard_users()
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
    service_method_result = UserDomainModel.get_ready_to_unblock_users()
    orm_query_result = user_model.objects.filter(
        blocked_until__isnull=False,
        blocked_until__lt=timezone.now()
    )

    assert service_method_result.count() == orm_query_result.count()
    assert list(service_method_result) == list(orm_query_result)
    assert all(user.is_blocked for user in service_method_result)


def test_unblock_users(user_model, ready_to_unblock_user):
    orm_fetched_user = user_model.objects.get(id=ready_to_unblock_user.id)
    assert orm_fetched_user.is_blocked

    UserDomainModel.unblock_users()

    refreshed_orm_fetched_user = user_model.objects.get(id=ready_to_unblock_user.id)

    assert not refreshed_orm_fetched_user.is_blocked


def test_create_user(user_model, user_data):
    db_state_before_service_method = user_model.objects.count()
    new_user = UserDomainModel.create_user(user_data=user_data)

    db_state_after_service_method = user_model.objects.count()

    assert db_state_after_service_method > db_state_before_service_method
    assert user_model.objects.filter(id=new_user.id).exists()
    assert not new_user.is_active
