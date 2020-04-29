from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class DateFrameException(ValidationError):
    already_completed = 'already_completed'
    overlapping_pomodoro = 'overlapping_pomodoro'
    invalid_pomodoro_length = 'invalid_pomodoro_length'
    current_pomodoro_exists = 'current_pomodoro_exists'
    invalid_date_frame_type = 'invalid_date_frame_type'
    start_greater_than_end = 'start_greater_than_end'

    messages = {
        already_completed: _('The pomodoro is already completed.'),
        overlapping_pomodoro: _('Start datetime overlaps with existing pomodoros.'),
        invalid_pomodoro_length: _('The submitted pomodoro length is longer than the specified pomodoro length.'),
        current_pomodoro_exists: _('You cannot start pomodoro for this task because there is a pomodoro in progress.'),
        invalid_date_frame_type: _('The submitted date type frame is invalid.'),
        start_greater_than_end: _('Start date cannot be greater than end date.')
    }

    def __init__(self, message, code=None, params=None):
        self.code = code
        super().__init__(message, code, params)
