from copy import deepcopy
from datetime import datetime, timedelta
from typing import Optional

from django.core.exceptions import ValidationError
from django.utils import timezone

from pomodorr.frames.services.date_frame_service import force_finish_date_frame
from pomodorr.projects.exceptions import TaskException
from pomodorr.projects.models import Task, Project
from pomodorr.projects.selectors.task_selector import get_active_tasks_for_user


def is_task_name_available(project: Project, name: str, excluded=None) -> bool:
    query = get_active_tasks_for_user(user=project.user, project=project, name=name)
    if excluded is not None:
        return not query.exclude(id=excluded.id).exists()
    return not query.exists()


def pin_to_project(task: Task, project: Project, db_save: bool = True) -> Optional[Task]:
    if is_task_name_available(project=project, name=task.name):
        pinned_task = perform_pin(task=task, project=project, db_save=db_save)
        return pinned_task
    else:
        raise ValidationError({'name': [TaskException.messages[TaskException.task_duplicated]]},
                              code=TaskException.task_duplicated)


def perform_pin(task: Task, project: Project, db_save: bool = True) -> Task:
    pinned_task = task
    pinned_task.project = project

    if db_save:
        pinned_task.save()

    return pinned_task


def complete_task(task: Task, db_save=True) -> Task:
    check_task_already_completed(task=task)
    force_finish_date_frame(task_id=task.id)

    if task.repeat_duration is not None:
        archived_task = archive_task(task=task)
        create_next_task(task=archived_task)
        return archived_task
    else:
        task.status = Task.status_completed
        if db_save:
            task.save()
        return task


def create_next_task(task: Task) -> Task:
    next_task = deepcopy(task)
    next_task.id = None
    next_due_date = get_next_due_date(due_date=task.due_date, duration=task.repeat_duration)
    next_task.due_date = next_due_date
    next_task.status = Task.status_active
    next_task.save()
    return next_task


def archive_task(task: Task) -> Task:
    archived_task = task
    archived_task.status = Task.status_completed
    archived_task.save()
    return archived_task


def reactivate_task(task: Task, db_save=True) -> Task:
    check_task_already_active(task=task)
    if not is_task_name_available(project=task.project, name=task.name):
        raise ValidationError([TaskException.messages[TaskException.task_duplicated]],
                              code=TaskException.task_duplicated)

    if task.due_date is None:
        task.due_date = get_next_due_date(due_date=task.due_date, duration=task.repeat_duration)

    task.status = Task.status_active

    if db_save:
        task.save()
    return task


def get_next_due_date(due_date: datetime, duration: timedelta) -> datetime:
    if due_date is None:
        return timezone.now()
    return due_date + duration


def check_task_already_completed(task: Task) -> None:
    if task.status == Task.status_completed:
        raise ValidationError([TaskException.messages[TaskException.already_completed]],
                              code=TaskException.already_completed)


def check_task_already_active(task: Task) -> None:
    if task.status == Task.status_active:
        raise ValidationError([TaskException.messages[TaskException.already_active]],
                              code=TaskException.already_active)
