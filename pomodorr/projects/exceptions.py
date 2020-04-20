from django.core.exceptions import ValidationError


class TaskException(ValidationError):
    pass
