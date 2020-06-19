import pytest

pytestmark = pytest.mark.django_db


def test_create_user(user_model, user_data):
    db_state_before_service_method = user_model.objects.count()
    new_user = user_model.objects.create_user(**user_data)

    db_state_after_service_method = user_model.objects.count()

    assert db_state_after_service_method > db_state_before_service_method
    assert user_model.objects.filter(id=new_user.id).exists()
    assert not new_user.is_active


def test_is_blocked_annotation(user_model, active_user, blocked_user):
    orm_fetched_blocked_user = user_model.objects.get(id=blocked_user.id)
    orm_fetched_active_user = user_model.objects.get(id=active_user.id)

    assert orm_fetched_blocked_user.is_blocked is True
    assert orm_fetched_active_user.is_blocked is False


def test_get_active_standard_users(user_model, active_user, non_active_user, blocked_user, admin_user):
    orm_fetched_active_users = user_model.objects.active_standard_users()

    assert len(orm_fetched_active_users) == 1
    assert active_user in orm_fetched_active_users


def test_get_non_active_standard_users(user_model, active_user, non_active_user, blocked_user, admin_user):
    orm_fetched_non_active_users = user_model.objects.non_active_standard_users()

    assert len(orm_fetched_non_active_users) == 1
    assert non_active_user in orm_fetched_non_active_users


def test_get_blocked_standard_users(user_model, active_user, non_active_user, blocked_user, admin_user):
    orm_fetched_blocked_users = user_model.objects.blocked_standard_users()

    assert len(orm_fetched_blocked_users) == 1
    assert blocked_user in orm_fetched_blocked_users


def test_get_ready_to_unblock_users(user_model, active_user, non_active_user, blocked_user, admin_user,
                                    ready_to_unblock_user):
    orm_fetched_ready_to_unblock_users = user_model.objects.ready_to_unblock_users()

    assert len(orm_fetched_ready_to_unblock_users) == 1
    assert ready_to_unblock_user in orm_fetched_ready_to_unblock_users
