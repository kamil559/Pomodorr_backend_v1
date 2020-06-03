import factory
import pytest

from pomodorr.user_settings.models import UserSetting


@pytest.mark.django_db
def test_user_settings_is_created_after_user_created(user_model, user_data):
    new_user = user_model.objects.create_user(**user_data)

    assert UserSetting.objects.filter(user=new_user).exists()


@pytest.mark.django_db
def test_user_settings_is_not_created_after_update(user_model, active_user):
    assert UserSetting.objects.count() == 1

    active_user.email = factory.Faker("email")
    active_user.save()

    assert UserSetting.objects.count() == 1


@pytest.mark.django_db
def test_user_settings_is_not_created_for_admin(user_model, admin_data):
    new_admin = user_model.objects.create_superuser(**admin_data)

    assert UserSetting.objects.filter(user=new_admin).exists() is False
