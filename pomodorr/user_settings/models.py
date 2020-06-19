import uuid
from datetime import timedelta

from django.db import models


class UserSetting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pomodoro_length = models.DurationField(blank=False, null=False, default=timedelta(minutes=25))
    short_break_length = models.DurationField(blank=False, null=False, default=timedelta(minutes=5))
    long_break_length = models.DurationField(blank=False, null=False, default=timedelta(minutes=15))
    long_break_after = models.SmallIntegerField(blank=False, null=False, default=3)
    auto_pomodoro_start = models.BooleanField(blank=False, null=False, default=False)
    auto_break_start = models.BooleanField(blank=False, null=False, default=False)
    disable_breaks = models.BooleanField(blank=False, null=False, default=False)

    user = models.OneToOneField(to='users.User', blank=False, null=False, on_delete=models.CASCADE,
                                related_name='settings')

    def __str__(self):
        return f'{self.user.email}\'s settings'
