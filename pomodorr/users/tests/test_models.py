from datetime import timedelta, datetime

import pytest
from pomodorr.users.tests.factories import prepare_user

pytestmark = pytest.mark.django_db


def test_is_blocked_annotation(user_model):
    blocked_user = prepare_user(number_of_users=1, blocked_until=datetime.now() + timedelta(hours=1))[0]
    orm_fetched_blocked_user = user_model.objects.get(id=blocked_user.id)

    assert hasattr(orm_fetched_blocked_user, "is_blocked")
    assert orm_fetched_blocked_user.is_blocked is True

    active_user = prepare_user(number_of_users=1, is_active=True)[0]
    orm_fetched_active_user = user_model.objects.get(id=active_user.id)

    assert hasattr(orm_fetched_active_user, "is_blocked")
    assert orm_fetched_active_user.is_blocked is False


def test_get_active_standard_users(user_model):
    active_users = prepare_user(number_of_users=2, is_active=True)
    prepare_user(number_of_users=1)
    prepare_user(number_of_users=1, is_active=True, is_superuser=True)
    prepare_user(number_of_users=1, is_active=True, is_staff=True)
    orm_fetched_active_users = user_model.objects.active_standard_users()

    assert len(orm_fetched_active_users) == 2
    assert list(orm_fetched_active_users) == active_users


def test_get_non_active_standard_users(user_model):
    non_active_users = prepare_user(number_of_users=2)
    prepare_user(number_of_users=2, is_active=True)
    prepare_user(number_of_users=1, is_superuser=True)
    prepare_user(number_of_users=1, is_staff=True)
    orm_fetched_non_active_users = user_model.objects.non_active_standard_users()

    assert len(orm_fetched_non_active_users) == 2
    assert list(orm_fetched_non_active_users) == non_active_users


def test_get_blocked_standard_users(user_model):
    blocked_users = prepare_user(number_of_users=2, blocked_until=datetime.now() + timedelta(hours=1))
    prepare_user(number_of_users=1, is_active=True)
    prepare_user(number_of_users=1, is_active=True, is_superuser=True)
    prepare_user(number_of_users=1, is_active=True, is_staff=True)
    orm_fetched_blocked_users = user_model.objects.blocked_standard_users()

    assert len(orm_fetched_blocked_users) == 2
    assert list(orm_fetched_blocked_users) == blocked_users


def test_get_ready_to_unblock_users(user_model):
    ready_to_unblock_users = prepare_user(number_of_users=2, blocked_until=datetime.now() - timedelta(seconds=1))
    prepare_user(number_of_users=2, blocked_until=datetime.now() + timedelta(hours=1))
    prepare_user(number_of_users=1, is_active=True)
    prepare_user(number_of_users=1, is_active=True, is_superuser=True)
    prepare_user(number_of_users=1, is_active=True, is_staff=True)
    orm_fetched_ready_to_unblock_users = user_model.objects.ready_to_unblock_users()

    assert len(orm_fetched_ready_to_unblock_users) == 2
    assert list(orm_fetched_ready_to_unblock_users) == ready_to_unblock_users
