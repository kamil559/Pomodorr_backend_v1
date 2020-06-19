from django.contrib.auth import get_user_model

from config import celery_app


@celery_app.task(name='pomodorr.users.unblock_users')
def unblock_users() -> None:
    User = get_user_model()

    User.objects.ready_to_unblock_users().update(blocked_until=None)
