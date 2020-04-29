from django.contrib import admin

from pomodorr.frames.models import TaskEvent


@admin.register(TaskEvent)
class TaskEventAdmin(admin.ModelAdmin):
    pass
