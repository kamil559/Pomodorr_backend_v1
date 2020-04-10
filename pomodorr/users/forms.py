from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UsernameField, UserChangeForm
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class AdminSiteUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete': 'email'})
    )

    def clean_username(self):
        username = self.cleaned_data.get("username", None) or None

        if username is not None and User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(_("Username is not available. Please type a different username."))
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email", None) or None

        if email is not None and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("Email is not available. Please type a different email."))
        return email

    def clean_blocked_until(self):
        blocked_until = self.cleaned_data.get("blocked_until", None) or None

        if blocked_until is not None:
            blocked_until = timezone.localtime(blocked_until)
            if blocked_until < timezone.now():
                raise forms.ValidationError(_("This datetime value cannot be lower than the actual date and time."))

        return blocked_until

    class Meta:
        model = get_user_model()
        fields = ("username", "email", "blocked_until")
        field_classes = {'username': UsernameField}


class AdminSiteUserUpdateForm(UserChangeForm):

    def clean_blocked_until(self):
        blocked_until = self.cleaned_data.get("blocked_until", None) or None

        if blocked_until is not None:
            blocked_until = timezone.localtime(blocked_until)
            if blocked_until < timezone.now():
                raise forms.ValidationError(_("This datetime value cannot be lower than the actual date and time."))

        return blocked_until

    def save(self, commit=True):
        return super(AdminSiteUserUpdateForm, self).save(commit=commit)

    class Meta:
        model = get_user_model()
        fields = ("username", "email", "blocked_until")
        field_classes = {'username': UsernameField}
