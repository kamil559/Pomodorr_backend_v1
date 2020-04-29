from pomodorr.frames.models import TaskEvent


class TaskEventSelector:
    model = TaskEvent

    @classmethod
    def get_all_task_events(cls, **kwargs):
        return cls.model.objects.all(**kwargs)

    @classmethod
    def get_all_task_events_for_user(cls, user, **kwargs):
        return cls.model.objects.filter(task__project__user=user, **kwargs)

    @classmethod
    def get_all_task_events_for_project(cls, project, **kwargs):
        return cls.model.objects.filter(task__project=project, **kwargs)

    @classmethod
    def get_all_task_events_for_task(cls, task, **kwargs):
        return cls.model.objects.filter(task=task, **kwargs)

    @classmethod
    def get_active_task_events_for_task(cls, task, **kwargs):
        return cls.model.objects.filter(task=task, start__isnull=False, end__isnull=True, **kwargs)

    @classmethod
    def get_current_task_event_for_task(cls, task):
        due_date = task.due_date

        if due_date is not None:
            current_task_event = task.events.filter(
                created_at__date=due_date.date(),
                start__isnull=False,
                end__isnull=True
            ).order_by('-created_at').first()
        else:
            current_task_event = task.events.filter(
                start__isnull=False,
                end__isnull=True
            ).order_by('-created_at').first()

        return current_task_event
