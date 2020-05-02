from copy import deepcopy
from datetime import datetime

from django.core.exceptions import ValidationError
from django.utils import timezone

from pomodorr.frames.exceptions import DateFrameException as DFE
from pomodorr.frames.models import DateFrame
from pomodorr.frames.selectors import DateFrameSelector
from pomodorr.projects.exceptions import TaskException
from pomodorr.projects.models import Project, Task, SubTask
from pomodorr.projects.selectors import ProjectSelector, TaskSelector, SubTaskSelector


class ProjectServiceModel:
    model = Project
    selector_class = ProjectSelector

    @classmethod
    def is_project_name_available(cls, user, name, exclude=None):
        query = cls.selector_class.get_active_projects_for_user(user=user, name=name)
        if exclude is not None:
            return not query.exclude(id=exclude.id).exists()
        return not query.exists()


class TaskServiceModel:

    def __init__(self):
        self.model = Task
        self.task_selector = TaskSelector
        self.date_frame_selector = DateFrameSelector(model_class=DateFrame)

    def is_task_name_available(self, project, name, exclude=None):
        query = self.task_selector.get_active_tasks_for_user(user=project.user, project=project, name=name)
        if exclude is not None:
            return not query.exclude(id=exclude.id).exists()
        return not query.exists()

    def pin_to_project(self, task, project, db_save=True):
        if self.is_task_name_available(project=project, name=task.name):
            pinned_task = self.perform_pin(task=task, project=project, db_save=db_save)
            return pinned_task
        else:
            raise ValidationError({'name': [TaskException.messages[TaskException.task_duplicated]]},
                                  code=TaskException.task_duplicated)

    @staticmethod
    def perform_pin(task, project, db_save=True):
        pinned_task = task
        pinned_task.project = project

        if db_save:
            pinned_task.save()

        return pinned_task

    def complete_task(self, task, db_save=True):
        now = timezone.now()
        self.check_task_already_completed(task=task)
        colliding_date_frame = self.date_frame_selector.get_colliding_date_frame_for_task(
            task=task, end=now, is_adding=False)

        if colliding_date_frame is not None:
            self.finish_colliding_date_frame(colliding_date_frame=colliding_date_frame, now=now)

        if task.repeat_duration is not None:
            archived_task = self.archive_task(task=task)
            self.create_next_task(task=archived_task)
            return archived_task
        else:
            task.status = self.model.status_completed
            if db_save:
                task.save()
            return task

    def create_next_task(self, task):
        next_task = deepcopy(task)
        next_task.id = None
        next_due_date = self.get_next_due_date(due_date=task.due_date, duration=task.repeat_duration)
        next_task.due_date = next_due_date
        next_task.status = self.model.status_active
        next_task.save()
        return next_task

    @staticmethod
    def archive_task(task):
        archived_task = task
        archived_task.status = Task.status_completed
        archived_task.save()
        return archived_task

    def reactivate_task(self, task, db_save=True):
        self.check_task_already_active(task=task)
        if not self.is_task_name_available(project=task.project, name=task.name):
            raise ValidationError([TaskException.messages[TaskException.task_duplicated]],
                                  code=TaskException.task_duplicated)

        task.status = self.model.status_active
        if db_save:
            task.save()
        return task

    @staticmethod
    def get_next_due_date(due_date, duration):
        if due_date is None:
            return timezone.now()
        return due_date + duration

    def check_task_already_completed(self, task):
        if task.status == self.model.status_completed:
            raise ValidationError([TaskException.messages[TaskException.already_completed]],
                                  code=TaskException.already_completed)

    def check_task_already_active(self, task):
        if task.status == self.model.status_active:
            raise ValidationError([TaskException.messages[TaskException.already_active]],
                                  code=TaskException.already_active)

    def finish_colliding_date_frame(self, colliding_date_frame: DateFrame, now: datetime) -> None:
        estimated_end = self.get_estimated_date_frame_end(colliding_date_frame=colliding_date_frame)
        if self.check_can_finish_date_frame(colliding_date_frame=colliding_date_frame, checked_date=now,
                                            estimated_date_frame_end=estimated_end):
            colliding_date_frame.end = estimated_end
            colliding_date_frame.save()
        else:
            raise ValidationError({'__all__': DFE.messages[DFE.overlapping_date_frame]},
                                  code=DFE.overlapping_date_frame)

    def check_can_finish_date_frame(self, colliding_date_frame: DateFrame, checked_date: datetime,
                                    estimated_date_frame_end: datetime):
        if self.check_is_pause_type(colliding_date_frame=colliding_date_frame):
            return True

        if colliding_date_frame is not None:
            if colliding_date_frame.end is not None:
                return False
            else:
                return checked_date > estimated_date_frame_end
        return True

    @staticmethod
    def get_estimated_date_frame_end(colliding_date_frame: DateFrame):
        if colliding_date_frame.end is not None:
            return colliding_date_frame.end
        return colliding_date_frame.start + colliding_date_frame.normalized_date_frame_length

    @staticmethod
    def check_is_pause_type(colliding_date_frame: DateFrame) -> bool:
        return colliding_date_frame.frame_type == DateFrame.pause_type


class SubTaskServiceModel:
    model = SubTask
    task_selector = SubTaskSelector

    def is_sub_task_name_available(self, task, name, exclude=None):
        query = self.task_selector.get_all_sub_tasks_for_task(task=task, name=name)
        if exclude is not None:
            return not query.exclude(id=exclude.id).exists()
        return not query.exists()
