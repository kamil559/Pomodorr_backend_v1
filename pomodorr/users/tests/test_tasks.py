import pytest

from pomodorr.users.tasks import unblock_users


@pytest.mark.django_db
def test_unblock_users(user_model, ready_to_unblock_user):
    assert user_model.objects.ready_to_unblock_users().exists()

    unblock_users.apply()

    assert user_model.objects.ready_to_unblock_users().exists() is False
