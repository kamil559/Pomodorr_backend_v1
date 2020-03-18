import pytest

from pomodorr.users.forms import AdminSiteUserCreationForm
from pomodorr.users.tests.factories import prepare_registration_data


@pytest.mark.django_db
def test_clean_username():
    registration_data = prepare_registration_data()

    form = AdminSiteUserCreationForm({
        "email": registration_data.get("email"),
        "username": registration_data.get("username"),
        "password1": registration_data.get("password"),
        "password2": registration_data.get("password2")
    })

    assert form.is_valid()
    assert form.cleaned_data.get("username") == registration_data.get("username")
    assert form.cleaned_data.get("email") == registration_data.get("email")

    user_instance = form.save()

    assert user_instance.check_password(registration_data.get("password")) == True

    form = AdminSiteUserCreationForm({
        "email": registration_data.get("email"),
        "username": registration_data.get("username"),
        "password1": registration_data.get("password"),
        "password2": registration_data.get("password2")
    })

    assert not form.is_valid()
    assert len(form.errors) == 2
    assert "email" in form.errors
    assert "username" in form.errors
