from django.apps import AppConfig
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _

from pomodorr.users.signals.handlers import create_default_project


class UsersConfig(AppConfig):
    name = "pomodorr.users"
    verbose_name = _("Users")

    def ready(self):
        try:
            from pomodorr.users.signals.handlers import create_settings
            user_model = self.get_model('User', require_ready=True)

            post_save.connect(receiver=create_settings, sender=user_model,
                              dispatch_uid='pomodorr.users.signals.create_settings')

            post_save.connect(receiver=create_default_project, sender=user_model,
                              dispatch_uid='pomodorr.users.signals.create_default_project')

        except ImportError:
            pass  # noqa F401
