from typing import Union

from model_utils.managers import SoftDeletableQuerySetMixin

from pomodorr.projects.models import Project, CustomSoftDeletableQueryset, Priority, Task, SubTask, TaskEvent, Gap


class ProjectSelector:
    model = Project

    @classmethod
    def get_active_projects_for_user(cls, user, **kwargs):
        return cls.model.objects.filter(user=user, **kwargs)

    @classmethod
    def get_removed_projects_for_user(cls, user, **kwargs):
        return cls.model.all_objects.filter(is_removed=True, user=user, **kwargs)

    @classmethod
    def get_all_projects_for_user(cls, user, **kwargs):
        return cls.model.all_objects.filter(user=user, **kwargs)

    @classmethod
    def get_all_active_projects(cls, **kwargs):
        return cls.model.objects.all(**kwargs)

    @classmethod
    def get_all_removed_projects(cls, **kwargs):
        return cls.model.all_objects.filter(is_removed=True, **kwargs)

    @classmethod
    def get_all_projects(cls, **kwargs):
        return cls.model.all_objects.all(**kwargs)

    @classmethod
    def hard_delete_on_queryset(cls, queryset: Union[CustomSoftDeletableQueryset, SoftDeletableQuerySetMixin]) -> None:
        queryset.delete(soft=False)

    @classmethod
    def undo_delete_on_queryset(cls, queryset: Union[CustomSoftDeletableQueryset, SoftDeletableQuerySetMixin]) -> None:
        queryset.update(is_removed=False)


class PrioritySelector:
    model = Priority

    @classmethod
    def get_all_priorities(cls, **kwargs):
        return cls.model.objects.all().filter(**kwargs)

    @classmethod
    def get_priorities_for_user(cls, user, **kwargs):
        return cls.model.objects.filter(user=user, **kwargs)


class TaskSelector:
    model = Task

    @classmethod
    def get_active_tasks(cls, **kwargs):
        return cls.model.objects.filter(status=0, **kwargs)

    @classmethod
    def get_completed_tasks(cls, **kwargs):
        return cls.model.objects.filter(status=1, **kwargs)

    @classmethod
    def get_removed_tasks(cls, **kwargs):
        return cls.model.all_objects.filter(is_removed=True, **kwargs)

    @classmethod
    def get_all_tasks(cls, **kwargs):
        return cls.model.all_objects.all(**kwargs)

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
    def get_all_non_removed_tasks_for_user(cls, user, **kwargs):
        return cls.model.objects.filter(project__user=user, **kwargs)

    @classmethod
    def get_all_tasks_for_user(cls, user, **kwargs):
        return cls.model.all_objects.filter(project__user=user, **kwargs)


class SubTaskSelector:
    model = SubTask

    @classmethod
    def get_all_sub_tasks(cls, **kwargs):
        return cls.model.objects.all(**kwargs)

    @classmethod
    def get_all_sub_tasks_for_task(cls, task, **kwargs):
        return cls.model.objects.filter(task=task, **kwargs)


class TaskEventSelector:
    model = TaskEvent

    @classmethod
    def get_all_task_events(cls, **kwargs):
        return cls.model.objects.all(**kwargs)

    @classmethod
    def get_all_task_events_for_user(cls, user, **kwargs):
        return cls.model.objects.filter(task__project__user=user, **kwargs)

    @classmethod
    def get_all_task_events_for_project(cls, project, **kwargs):
        return cls.model.objects.filter(task__project=project, **kwargs)

    @classmethod
    def get_all_task_events_for_task(cls, task, **kwargs):
        return cls.model.objects.filter(task=task, **kwargs)

    @classmethod
    def get_active_task_events_for_task(cls, task, **kwargs):
        return cls.model.objects.filter(task=task, start__isnull=False, end__isnull=True, **kwargs)

    @classmethod
    def get_current_task_event_for_task(cls, task):
        due_date = task.due_date

        if due_date is not None:
            current_task_event = task.events.filter(
                created_at__date=due_date.date(),
                start__isnull=False,
                end__isnull=True
            ).order_by('-created_at').first()
        else:
            current_task_event = task.events.filter(
                start__isnull=False,
                end__isnull=True
            ).order_by('-created_at').first()

        return current_task_event


class GapSelector:
    model = Gap

    @classmethod
    def get_all_gaps(cls, **kwargs):
        return cls.model.objects.all(**kwargs)

    @classmethod
    def get_finished_gaps(cls, **kwargs):
        return cls.model.objects.filter(start__isnull=False, end__isnull=False, **kwargs)

    @classmethod
    def get_unfinished_gaps(cls, **kwargs):
        return cls.model.objects.filter(start__isnull=False, end__isnull=True, **kwargs)
