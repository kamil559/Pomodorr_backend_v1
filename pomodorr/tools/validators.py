from django.conf import settings
from django.core.exceptions import ValidationError

from pomodorr.projects.exceptions import TaskException


def validate_image(file_object):
    file_size = file_object.size
    max_size = settings.MAX_UPLOAD_SIZE
    if file_size > max_size:
        raise ValidationError("The file size have been exceeded. Max file size is %sMB" % str(max_size / 1024 / 1024))


def duration_validation(value):
    total_hours = value.total_seconds() / 60 / 60
    if total_hours % 24:
        raise ValidationError(TaskException.messages[TaskException.invalid_duration])
