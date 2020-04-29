from django.db import models


class PomodoroManager(models.Manager):
    def get_queryset(self):
        return super(PomodoroManager, self).get_queryset().filter(type=0)


class BreakManager(models.Manager):
    def get_queryset(self):
        return super(BreakManager, self).get_queryset().filter(type=1)


class PauseManager(models.Manager):
    def get_queryset(self):
        return super(PauseManager, self).get_queryset().filter(type=2)
