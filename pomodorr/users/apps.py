from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "pomodorr.users"
    verbose_name = _("Users")

    def ready(self):
        try:
            import pomodorr.users.signals.handlers  # noqa F401
        except ImportError:
            pass
