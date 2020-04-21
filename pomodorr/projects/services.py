from copy import deepcopy

from django.utils import timezone
from django.utils.translation import gettext as _

from pomodorr.projects.exceptions import TaskException, TaskEventException
from pomodorr.projects.models import Project, Task, SubTask
from pomodorr.projects.selectors import ProjectSelector, TaskSelector, TaskEventSelector, SubTaskSelector


class ProjectServiceModel:
    model = Project
    selector_class = ProjectSelector

    @classmethod
    def is_project_name_available(cls, user, name, exclude_id=None):
        query = cls.selector_class.get_active_projects_for_user(user=user, name=name)
        if exclude_id is not None:
            return not query.exclude(id=exclude_id).exists()
        return not query.exists()


class TaskServiceModel:
    model = Task
    task_selector = TaskSelector
    task_event_selector = TaskEventSelector

    def is_task_name_available(self, project, name, exclude_id=None):
        query = self.task_selector.get_active_tasks_for_user(user=project.user, project=project, name=name)
        if exclude_id is not None:
            return not query.exclude(id=exclude_id).exists()
        return not query.exists()

    def can_pin_to_project(self, task, project):
        is_task_existent = self.task_selector.get_all_tasks_for_user(user=project.user, project=project,
                                                                     name=task.name).exists()

        return not is_task_existent

    def pin_to_project(self, task, project, preserve_statistics=False):
        if self.can_pin_to_project(task=task, project=project):

            if preserve_statistics:
                task = self.perform_pin_with_preserving_statistics(task=task, project=project)
            else:
                task = self.perform_simple_pin(task=task, project=project)

            return task

        else:
            raise TaskException({'name': [_('There is already a task with identical name in the selected project')]},
                                code=TaskException.task_duplicated)

    @staticmethod
    def perform_pin_with_preserving_statistics(task, project):
        new_task = deepcopy(task)
        new_task.id = None
        new_task.project = project
        new_task.save()

        new_task.events.all().delete()

        task.delete()  # task is soft-deleted
        return new_task

    @staticmethod
    def perform_simple_pin(task, project):
        task.project = project
        task.save()
        return task

    def complete_task(self, task, active_task_event=None):
        self.check_task_already_completed(task=task)

        if active_task_event is not None:
            self.save_state_of_active_pomodoro(task_event=active_task_event)

        if task.repeat_duration is not None:
            next_due_date = self.get_next_due_date(due_date=task.due_date, duration=task.repeat_duration)
            task.due_date = next_due_date
            task.save()
        else:
            task.status = self.model.status_completed
            task.save()

    def reactivate_task(self, task):
        self.check_task_already_active(task=task)

        task.status = self.model.status_active
        task.save()

    @staticmethod
    def get_next_due_date(due_date, duration):
        if due_date is None:
            return timezone.now()
        return due_date + duration

    def check_task_already_completed(self, task):
        if task.status == self.model.status_completed:
            raise TaskException({'status': [_('The task is already completed.')]}, code=TaskException.already_completed)

    def check_task_already_active(self, task):
        if task.status == self.model.status_active:
            raise TaskException({'status': [_('The task is already active.')]}, code=TaskException.already_active)

    @staticmethod
    def save_state_of_active_pomodoro(task_event):
        if task_event.end is not None:
            raise TaskEventException({'__all__': [_('The pomodoro is already completed.')]},
                                     code=TaskEventException.already_completed)
        else:
            task_event.end = timezone.now()
            task_event.save()


class SubTaskService:
    model = SubTask
    task_selector = SubTaskSelector

    def is_sub_task_name_available(self, task, name, exclude_id=None):
        query = self.task_selector.get_all_sub_tasks_for_task(task=task, name=name)
        if exclude_id is not None:
            return not query.exclude(id=exclude_id).exists()
        return not query.exists()
