from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class DateFrameException(ValidationError):
    task_already_completed = 'task_already_completed'
    already_completed = 'already_completed'
    overlapping_date_frame = 'overlapping_date_frame'
    invalid_pomodoro_length = 'invalid_pomodoro_length'
    current_pomodoro_exists = 'current_pomodoro_exists'
    invalid_date_frame_type = 'invalid_date_frame_type'
    start_greater_than_end = 'start_greater_than_end'
    invalid_break_length = 'invalid_break_length'

    messages = {
        task_already_completed: _('You cannot submit date frame for a completed task.'),
        already_completed: _('The date frame is already completed.'),
        overlapping_date_frame: _('There is already a colliding date frame.'),
        invalid_pomodoro_length: _('The submitted pomodoro length is longer than the specified pomodoro length.'),
        invalid_break_length: _('The submitted break length is longer than the specified break length.'),
        current_pomodoro_exists: _('You cannot start pomodoro for this task because there is a pomodoro in progress.'),
        invalid_date_frame_type: _('The submitted date type frame is invalid.'),
        start_greater_than_end: _('Start date cannot be greater than end date.')
    }

    def __init__(self, message, code=None, params=None):
        super().__init__(message, code, params)
        self.code = code
