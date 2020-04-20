from copy import deepcopy

from django.utils.translation import gettext as _

from pomodorr.projects.exceptions import TaskException
from pomodorr.projects.models import Project, Task
from pomodorr.projects.selectors import ProjectSelector, TaskSelector


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
    selector_class = TaskSelector

    def is_task_name_available(self, project, name, exclude_id=None):
        query = self.selector_class.get_active_tasks_for_user(user=project.user, project=project, name=name)
        if exclude_id is not None:
            return not query.exclude(id=exclude_id).exists()
        return not query.exists()

    def can_pin_to_project(self, task, project):
        is_task_existent = self.selector_class.get_all_tasks_for_user(user=project.user, project=project,
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
            raise TaskException({'name': [_('There is already a task with identical name in the selected project')]})
            # todo: exception should be raised by can_pin_to_project

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
