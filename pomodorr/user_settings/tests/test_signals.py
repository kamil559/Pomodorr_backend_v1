import factory
import pytest

from pomodorr.user_settings.models import UserSetting

pytestmark = pytest.mark.django_db


def test_user_settings_is_created_after_user_created(user_model, user_data):
    new_user = user_model.objects.create_user(**user_data)

    assert UserSetting.objects.filter(user=new_user).exists()


def test_user_settings_is_not_created_after_user_updated(user_model, active_user):
    assert UserSetting.objects.count() == 1

    active_user.email = factory.Faker("email").generate()
    active_user.save()

    assert UserSetting.objects.count() == 1


def test_user_settings_is_not_created_after_admin_created(user_model, admin_data):
    new_admin = user_model.objects.create_superuser(**admin_data)

    assert UserSetting.objects.filter(user=new_admin).exists() is False
