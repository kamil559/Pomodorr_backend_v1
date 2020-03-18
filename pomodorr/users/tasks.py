from django.contrib.auth import get_user_model

from config import celery_app
from pomodorr.users.services import UserDomainModel

User = get_user_model()


@celery_app.task()
def get_users_count():
    """A pointless Celery task to demonstrate usage."""
    return User.objects.count()



@celery_app.task(name="unblock users", shared=False)
def unblock_users() -> None:
    UserDomainModel.unblock_users()
