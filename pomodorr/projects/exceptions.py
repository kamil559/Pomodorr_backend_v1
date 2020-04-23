from django.core.exceptions import ValidationError


class TaskException(ValidationError):
    already_active = 'already_active'
    already_completed = 'already_completed'
    task_duplicated = 'task_duplicated'

    def __init__(self, message, code=None, params=None):
        self.code = code
        super().__init__(message, code, params)


class TaskEventException(ValidationError):
    already_completed = 'already_completed'
    overlapping_pomodoro = 'overlapping_pomodoro'
    invalid_pomodoro_length = 'invalid_pomodoro_length'
    current_pomodoro_exists = 'current_pomodoro_exists'

    def __init__(self, message, code=None, params=None):
        self.code = code
        super().__init__(message, code, params)
