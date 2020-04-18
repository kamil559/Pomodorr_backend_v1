from typing import Union

from model_utils.managers import SoftDeletableQuerySetMixin

from pomodorr.projects.models import Project, CustomSoftDeletableQueryset, Priority, Task, SubTask, TaskEvent


class ProjectSelector:
    model = Project

    @classmethod
    def get_active_projects_for_user(cls, user, **kwargs):
        return cls.model.objects.filter(user=user, **kwargs)

    @classmethod
    def get_removed_projects_for_user(cls, user):
        return cls.model.all_objects.filter(is_removed=True, user=user)

    @classmethod
    def get_all_projects_for_user(cls, user):
        return cls.model.all_objects.filter(user=user)

    @classmethod
    def get_all_active_projects(cls):
        return cls.model.objects.all()

    @classmethod
    def get_all_removed_projects(cls):
        return cls.model.all_objects.filter(is_removed=True)

    @classmethod
    def get_all_projects(cls):
        return cls.model.all_objects.all()

    @classmethod
    def hard_delete_on_queryset(cls, queryset: Union[CustomSoftDeletableQueryset, SoftDeletableQuerySetMixin]) -> None:
        queryset.delete(soft=False)

    @classmethod
    def undo_delete_on_queryset(cls, queryset: Union[CustomSoftDeletableQueryset, SoftDeletableQuerySetMixin]) -> None:
        queryset.update(is_removed=False)


class PrioritySelector:
    model = Priority

    @classmethod
    def get_all_priorities(cls):
        return cls.model.objects.all()

    @classmethod
    def get_priorities_for_user(cls, user, **kwargs):
        return cls.model.objects.filter(user=user, **kwargs)


class TaskSelector:
    model = Task

    @classmethod
    def get_active_tasks(cls):
        return cls.model.objects.filter(status=0)

    @classmethod
    def get_completed_tasks(cls):
        return cls.model.objects.filter(status=1)

    @classmethod
    def get_removed_tasks(cls):
        return cls.model.all_objects.filter(is_removed=True)

    @classmethod
    def get_all_tasks(cls):
        return cls.model.all_objects.all()

    @classmethod
    def get_active_tasks_for_user(cls, user, **kwargs):
        return cls.model.objects.filter(status=0, project__user=user, **kwargs)

    @classmethod
    def get_completed_tasks_for_user(cls, user, **kwargs):
        return cls.model.objects.filter(status=1, project__user=user, **kwargs)

    @classmethod
    def get_removed_tasks_for_user(cls, user, **kwargs):
        return cls.model.all_objects.filter(is_removed=True, project__user=user, **kwargs)

    @classmethod
    def get_all_tasks_for_user(cls, user):
        return cls.model.all_objects.filter(project__user=user)


class SubTaskSelector:
    model = SubTask

    @classmethod
    def get_all_sub_tasks(cls):
        return cls.model.objects.all()

    @classmethod
    def get_all_sub_tasks_for_task(cls, task):
        return cls.model.objects.filter(task=task)


class TaskEventSelector:
    model = TaskEvent

    @classmethod
    def get_all_task_events(cls, **kwargs):
        return cls.model.objects.all()

    @classmethod
    def get_all_task_events_for_user(cls, user, **kwargs):
        return cls.model.objects.filter(task__project__user=user, **kwargs)

    @classmethod
    def get_all_task_events_for_project(cls, project, **kwargs):
        return cls.model.objects.filter(task__project=project, **kwargs)

    @classmethod
    def get_all_task_events_for_task(cls, task, **kwargs):
        return cls.model.objects.filter(task=task, **kwargs)
