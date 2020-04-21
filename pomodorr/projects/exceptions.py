from django.core.exceptions import ValidationError


class TaskException(ValidationError):
    already_active = 'already_active'
    already_completed = 'already_completed'
    task_duplicated = 'task_duplicated'

    pass


class TaskEventException(ValidationError):
    already_completed = 'already_completed'

    pass
