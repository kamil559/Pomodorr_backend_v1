from copy import deepcopy

from django.utils import timezone

from pomodorr.frames.exceptions import DateFrameException
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
    model = Task
    task_selector = TaskSelector
    task_event_selector = DateFrameSelector

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
            raise TaskException({'name': [TaskException.messages[TaskException.task_duplicated]]},
                                code=TaskException.task_duplicated)

    @staticmethod
    def perform_pin(task, project, db_save=True):
        pinned_task = task
        pinned_task.project = project

        if db_save:
            pinned_task.save()

        return pinned_task

    def complete_task(self, task, db_save=True):
        self.check_task_already_completed(task=task)
        active_task_event = self.task_event_selector.get_current_date_frame_for_task(task=task)

        if active_task_event is not None:
            self.save_state_of_active_pomodoro(task_event=active_task_event)

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
            raise TaskException([TaskException.messages[TaskException.task_duplicated]],
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
            raise TaskException([TaskException.messages[TaskException.already_completed]],
                                code=TaskException.already_completed)

    def check_task_already_active(self, task):
        if task.status == self.model.status_active:
            raise TaskException([TaskException.messages[TaskException.already_active]],
                                code=TaskException.already_active)

    @staticmethod
    def save_state_of_active_pomodoro(task_event):
        if task_event.end is not None:
            raise DateFrameException([DateFrameException.messages[DateFrameException.already_completed]],
                                     code=DateFrameException.already_completed)
        else:
            task_event.end = timezone.now()
            task_event.save()


class SubTaskServiceModel:
    model = SubTask
    task_selector = SubTaskSelector

    def is_sub_task_name_available(self, task, name, exclude=None):
        query = self.task_selector.get_all_sub_tasks_for_task(task=task, name=name)
        if exclude is not None:
            return not query.exclude(id=exclude.id).exists()
        return not query.exists()
