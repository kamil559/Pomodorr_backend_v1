import uuid
from collections import defaultdict

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from model_utils.fields import StatusField
from model_utils.models import TimeFramedModel, TimeStampedModel

from pomodorr.frames.managers import PomodoroManager, BreakManager, PauseManager


class DateFrame(TimeStampedModel):
    TYPE_CHOICES = [
        (0, 'pomodor'),
        (1, 'break'),
        (2, 'pause')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    start = models.DateTimeField(_('start'), blank=False, null=False, default=timezone.now)
    end = models.DateTimeField(_('end'), blank=True, null=True, default=None)
    duration = models.DurationField(blank=True, null=True, default=None)
    type = StatusField(blank=False, null=False, choices_name='TYPE_CHOICES')
    task = models.ForeignKey(to='projects.Task', null=False, blank=False, on_delete=models.CASCADE,
                             related_name='frames')

    def __str__(self):
        return f'{self.task.name}'

    class Meta:
        ordering = ('created',)
        verbose_name_plural = _('DateFrames')
        indexes = [
            models.Index(fields=['start', 'end'], condition=Q(start__isnull=False) & Q(end__isnull=False),
                         name='start_end_idx')
        ]

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.full_clean()
        super(DateFrame, self).save(force_insert=False, force_update=False, using=None, update_fields=None)

    def clean(self):
        self.clean_fields()

        errors_mapping = defaultdict(list)

        if self.start and self.end and self.start >= self.end:
            msg = _('Start date of the frame cannot be greater than end date.')
            errors_mapping['start'].append(msg)

        if errors_mapping:
            raise ValidationError(errors_mapping)


class Pomodoro(DateFrame):
    objects = PomodoroManager()

    class Meta:
        proxy = True


class Break(DateFrame):
    objects = BreakManager()

    class Meta:
        proxy = True


class Pause(DateFrame):
    objects = PauseManager()

    class Meta:
        proxy = True
