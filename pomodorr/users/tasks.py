from config import celery_app
from pomodorr.users.services import UserDomainModel


@celery_app.task(name='pomodorr.users.unblock_users')
def unblock_users() -> None:
    UserDomainModel.unblock_users()
