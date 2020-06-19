from django.contrib.auth.models import AbstractUser

from pomodorr.projects.models import Priority


def get_all_priorities(**kwargs):
    return Priority.objects.all().filter(**kwargs)


def get_priorities_for_user(user: AbstractUser, **kwargs):
    return Priority.objects.filter(user=user, **kwargs)
