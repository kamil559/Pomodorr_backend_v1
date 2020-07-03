from django.contrib.auth.models import AbstractUser

from pomodorr.projects.models import Task


def get_active_tasks(**kwargs):
    return Task.objects.filter(status=0, **kwargs)


def get_completed_tasks(**kwargs):
    return Task.objects.filter(status=1, **kwargs)


def get_removed_tasks(**kwargs):
    return Task.all_objects.filter(is_removed=True, **kwargs)


def get_all_non_removed_tasks(**kwargs):
    return Task.objects.filter(**kwargs)


def get_all_tasks(**kwargs):
    return Task.all_objects.all(**kwargs)


def get_active_tasks_for_user(user: AbstractUser, **kwargs):
    return Task.objects.filter(status=0, project__user=user, **kwargs)


def get_completed_tasks_for_user(user: AbstractUser, **kwargs):
    return Task.objects.filter(status=1, project__user=user, **kwargs)


def get_removed_tasks_for_user(user: AbstractUser, **kwargs):
    return Task.all_objects.filter(is_removed=True, project__user=user, **kwargs)


def get_all_non_removed_tasks_for_user(user: AbstractUser, **kwargs):
    return Task.objects.select_related('project__user', 'priority').prefetch_related('sub_tasks').filter(
        project__user=user, **kwargs).distinct()


def get_all_tasks_for_user(user: AbstractUser, **kwargs):
    return Task.all_objects.filter(project__user=user, **kwargs)
