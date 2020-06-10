import os
from datetime import timedelta

from celery import Celery
# set the default Django settings module for the 'celery' program.
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("pomodorr")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'clean-unfinished-date-frames-every-midnight': {
        'task': 'pomodorr.frames.clean_obsolete_date_frames',
        'schedule': crontab(
            hour=0,
            minute=0
        )
    },
    'unblock-ready-to-unblock-users-every-30-seconds': {
        'task': 'pomodorr.users.unblock_users',
        'schedule': timedelta(seconds=30)
    }
}
