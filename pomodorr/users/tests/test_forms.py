import pytest

from pomodorr.tools.utils import get_time_delta
from pomodorr.users.forms import AdminSiteUserCreationForm, AdminSiteUserUpdateForm

pytestmark = pytest.mark.django_db


def test_clean_username(user_registration_data):

    form = AdminSiteUserCreationForm(user_registration_data)

    assert form.is_valid()
    assert form.cleaned_data.get("username") == user_registration_data.get("username")
    assert form.cleaned_data.get("email") == user_registration_data.get("email")

    user_instance = form.save()

    assert user_instance.check_password(user_registration_data.get("password1"))

    form = AdminSiteUserCreationForm(user_registration_data)

    assert not form.is_valid()
    assert len(form.errors) == 2
    assert "email" in form.errors
    assert "username" in form.errors


def test_create_form_blocked_until_valid_datetime(user_model, user_registration_data):
    user_registration_data["blocked_until"] = get_time_delta({"days": 1})
    form = AdminSiteUserCreationForm(user_registration_data)

    assert form.is_valid()

    user_instance = form.save()

    assert user_instance.blocked_until is not None
    assert user_instance in user_model.objects.blocked_standard_users()


def test_create_form_blocked_until_invalid_datetime(user_model, user_registration_data):
    user_registration_data["blocked_until"] = get_time_delta({"days": 1}, ahead=False)
    form = AdminSiteUserCreationForm(user_registration_data)

    assert not form.is_valid()

    assert "blocked_until" in form.errors
    assert form.errors["blocked_until"][0] == "This datetime value cannot be lower than the actual date and time."

def test_update_form_blocked_until_valid_datetime(user_model, user_data, active_user):
    user_data["blocked_until"] = get_time_delta({"days": 1})
    user_data["date_joined"] = active_user.date_joined
    form = AdminSiteUserUpdateForm(instance=active_user, data=user_data)

    assert form.is_valid()

    user_instance = form.save()

    assert user_instance.blocked_until is not None
    assert user_instance in user_model.objects.blocked_standard_users()


def test_update_form_blocked_until_invalid_datetime(user_model, user_data, active_user):
    user_data["blocked_until"] = get_time_delta({"days": 1}, ahead=False)
    user_data["date_joined"] = active_user.date_joined
    form = AdminSiteUserUpdateForm(instance=active_user, data=user_data)

    assert not form.is_valid()

    assert "blocked_until" in form.errors
    assert form.errors["blocked_until"][0] == "This datetime value cannot be lower than the actual date and time."
