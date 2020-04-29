from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


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
