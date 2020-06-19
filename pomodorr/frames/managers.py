from django.db import models
from django.db.models import Case, When, Q, IntegerField


class DateFrameManager(models.Manager):
    def get_queryset(self):
        return super(DateFrameManager, self).get_queryset().annotate(
            is_finished=Case(
                When(Q(start__isnull=False) & Q(end__isnull=False), then=1), default=0,
                output_field=IntegerField()
            )
        )


class PomodoroManager(DateFrameManager):
    def get_queryset(self):
        return super(PomodoroManager, self).get_queryset().filter(type=0)


class BreakManager(DateFrameManager):
    def get_queryset(self):
        return super(BreakManager, self).get_queryset().filter(type=1)


class PauseManager(DateFrameManager):
    def get_queryset(self):
        return super(PauseManager, self).get_queryset().filter(type=2)
