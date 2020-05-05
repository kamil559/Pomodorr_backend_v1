import math
import uuid
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeFramedModel, TimeStampedModel

from pomodorr.frames.exceptions import DateFrameException as DFE
from pomodorr.frames.managers import PomodoroManager, BreakManager, PauseManager, DateFrameManager
from pomodorr.frames.selectors import DateFrameSelector
from pomodorr.frames.utils import DurationCalculatorLoader


class DateFrame(TimeStampedModel):
    pomodoro_type = 0
    break_type = 1
    pause_type = 2

    TYPE_CHOICES = [
        (pomodoro_type, _('pomodoro')),
        (break_type, _('break')),
        (pause_type, _('pause'))
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    start = models.DateTimeField(_('start'), blank=False, null=False, default=timezone.now)
    end = models.DateTimeField(_('end'), blank=True, null=True, default=None)
    duration = models.DurationField(blank=True, null=True, default=None)
    frame_type = models.SmallIntegerField(blank=False, null=False, choices=TYPE_CHOICES)
    task = models.ForeignKey(to='projects.Task', null=False, blank=False, on_delete=models.CASCADE,
                             related_name='frames')

    objects = DateFrameManager()

    def __init__(self, *args, **kwargs):
        super(DateFrame, self).__init__(*args, **kwargs)
        self.selector_class = DateFrameSelector(model_class=self.__class__)

    def __str__(self):
        return f'{self.get_frame_type_display()}: {"finished" if self.start and self.end else "started"}'

    class Meta:
        ordering = ('created',)
        verbose_name = _('Date frame')
        verbose_name_plural = _('Date frames')
        indexes = [
            models.Index(fields=['start', 'end'], condition=Q(start__isnull=False) & Q(end__isnull=False),
                         name='start_end_idx')
        ]

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.clean_fields()
        self.full_clean()
        return super(DateFrame, self).save(force_insert, force_update, using, update_fields)

    def clean(self):
        if self.start and self.end:
            self.duration = self.normalized_duration

        additional_validators = [
            self.check_start_greater_than_end,
            self.check_task_is_already_completed,
            self.check_date_frame_duration_fits_error_margin
        ]

        for validator_method in additional_validators:
            validator_method()

    def check_start_greater_than_end(self):
        if self.start and self.end and self.start > self.end:
            raise ValidationError({'start': DFE.messages[DFE.start_greater_than_end]}, code=DFE.start_greater_than_end)

    def check_task_is_already_completed(self):
        if self.task and self.task.status == self.task.__class__.status_completed:
            raise ValidationError({'__all__': DFE.messages[DFE.task_already_completed]},
                                  code=DFE.task_already_completed)

    def check_date_frame_duration_fits_error_margin(self):
        if self.start and self.end and self.frame_type in {self.pomodoro_type, self.break_type}:
            duration_difference = self.duration - self.normalized_date_frame_length
            if self.frame_type == self.pomodoro_type:
                if duration_difference > settings.DATE_FRAME_ERROR_MARGIN:
                    raise ValidationError([DFE.messages[DFE.invalid_pomodoro_length]], code=DFE.invalid_pomodoro_length)

            elif self.frame_type == self.break_type:
                if duration_difference > settings.DATE_FRAME_ERROR_MARGIN:
                    raise ValidationError({'__all__': DFE.messages[DFE.invalid_break_length]},
                                          code=DFE.invalid_break_length)

    @property
    def normalized_duration(self) -> timedelta:
        duration_calculator = DurationCalculatorLoader(date_frame_object=self, end=self.end)
        duration = duration_calculator.calculate()
        truncated_minutes = math.trunc(duration.seconds / 60)
        return timedelta(minutes=truncated_minutes)

    @property
    def normalized_date_frame_length(self) -> timedelta:
        if self.frame_type == self.pomodoro_type:
            return self.task.normalized_pomodoro_length
        elif self.frame_type == self.break_type:
            return self.task.normalized_break_length
        else:
            return timedelta()


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
