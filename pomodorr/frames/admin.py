from django.contrib import admin

from pomodorr.frames.models import DateFrame


@admin.register(DateFrame)
class DateFrameAdmin(admin.ModelAdmin):
    pass
