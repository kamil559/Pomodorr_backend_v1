from django.contrib.auth.models import AbstractUser

from pomodorr.projects import models


def get_active_projects_for_user(user: AbstractUser, **kwargs):
    return models.Project.objects.filter(user=user, **kwargs)


def get_removed_projects_for_user(user: AbstractUser, **kwargs):
    return models.Project.all_objects.filter(is_removed=True, user=user, **kwargs)


def get_all_projects_for_user(user: AbstractUser, **kwargs):
    return models.Project.all_objects.filter(user=user, **kwargs)


def get_all_active_projects(**kwargs):
    return models.Project.objects.all(**kwargs)


def get_all_removed_projects(**kwargs):
    return models.Project.all_objects.filter(is_removed=True, **kwargs)


def get_all_projects(**kwargs):
    return models.Project.all_objects.all(**kwargs)


def hard_delete_on_queryset(queryset) -> None:
    queryset.delete(soft=False)


def undo_delete_on_queryset(queryset) -> None:
    queryset.update(is_removed=False)
