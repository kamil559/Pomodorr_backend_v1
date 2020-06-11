from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UserSettingsConfig(AppConfig):
    name = "pomodorr.user_settings"
    verbose_name = _("User Settings")
