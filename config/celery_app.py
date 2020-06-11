import os
from datetime import timedelta

from celery import Celery
# set the default Django settings module for the 'celery' program.
from celery.schedules import crontab
from kombu import Queue

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("pomodorr")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.broker_transport_options = {
    'queue_order_strategy': 'priority'
}

app.conf.task_queues = (
    Queue('users_tasks', routing_key='pomodorr.users.#', queue_arguments={'x-max-priority': 0}),
    Queue('frames_tasks', routing_key='pomodorr.frames.#', queue_arguments={'x-max-priority': 10})
)

app.conf.beat_schedule = {
    'clean-unfinished-date-frames-every-midnight': {
        'task': 'pomodorr.frames.clean_obsolete_date_frames',
        'schedule': crontab(
            hour=0,
            minute=0
        ),
        'options': {
            'queue': 'frames_tasks'
        }
    },
    'unblock-ready-to-unblock-users-every-30-seconds': {
        'task': 'pomodorr.users.unblock_users',
        'schedule': timedelta(seconds=30),
        'options': {
            'queue': 'users_tasks'
        }
    }
}
