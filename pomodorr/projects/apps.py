from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ProjectsConfig(AppConfig):
    name = 'pomodorr.projects'
    verbose = _('Projects')

    def ready(self):
        try:
            from pomodorr.projects.signals.dispatchers import notify_force_finish
            from pomodorr.projects.signals.handlers import task_completed_notify_channel

            notify_force_finish.connect(receiver=task_completed_notify_channel,
                                        dispatch_uid='pomodorr.projects.signals.task_completed_notify_channel')

        except ImportError:
            pass  # noqa F401
