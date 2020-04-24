from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class PriorityException(ValidationError):
    priority_duplicated = 'priority_duplicated'

    messages = {
        priority_duplicated: _('Priority name must be unique.')
    }


class ProjectException(ValidationError):
    project_duplicated = 'project_duplicated'
    priority_does_not_exist = 'priority_does_not_exist'

    messages = {
        project_duplicated: _('Project name must be unique.'),
        priority_does_not_exist: _('The chosen priority does not exist.'),
    }

    def __init__(self, message, code=None, params=None):
        self.code = code
        super().__init__(message, code, params)


class TaskException(ValidationError):
    already_active = 'already_active'
    already_completed = 'already_completed'
    task_duplicated = 'task_duplicated'
    priority_does_not_exist = 'priority_does_not_exist'
    project_does_not_exist = 'project_does_not_exist'

    messages = {
        task_duplicated: _('There is already a task with identical name in the selected project.'),
        already_completed: _('The task is already completed.'),
        already_active: _('The task is already active.'),
        priority_does_not_exist: _('The chosen priority does not exist.'),
        project_does_not_exist: _('The chosen project does not exist.')
    }

    def __init__(self, message, code=None, params=None):
        self.code = code
        super().__init__(message, code, params)


class TaskEventException(ValidationError):
    already_completed = 'already_completed'
    overlapping_pomodoro = 'overlapping_pomodoro'
    invalid_pomodoro_length = 'invalid_pomodoro_length'
    current_pomodoro_exists = 'current_pomodoro_exists'

    messages = {
        already_completed: _('The pomodoro is already completed.'),
        overlapping_pomodoro: _('Start datetime overlaps with existing pomodoros.'),
        invalid_pomodoro_length: _('The submitted pomodoro length is longer than the specified pomodoro length.'),
        current_pomodoro_exists: _('You cannot start pomodoro for this task because there is a pomodoro in progress.')
    }

    def __init__(self, message, code=None, params=None):
        self.code = code
        super().__init__(message, code, params)
