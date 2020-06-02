from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FramesConfig(AppConfig):
    name = 'pomodorr.frames'
    verbose = _('Frames')
