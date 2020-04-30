import math
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from model_utils.fields import StatusField
from model_utils.models import TimeFramedModel, TimeStampedModel

from pomodorr.frames.exceptions import DateFrameException as DFE
from pomodorr.frames.managers import PomodoroManager, BreakManager, PauseManager
from pomodorr.frames.selectors import DateFrameSelector


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
    type = StatusField(blank=False, null=False, choices_name='TYPE_CHOICES')
    task = models.ForeignKey(to='projects.Task', null=False, blank=False, on_delete=models.CASCADE,
                             related_name='frames')

    def __init__(self, *args, **kwargs):
        super(DateFrame, self).__init__(*args, **kwargs)
        self.selector_class = DateFrameSelector

    def __str__(self):
        return f'{self.task.name}'

    class Meta:
        ordering = ('created',)
        verbose_name = _('Date frame')
        verbose_name_plural = _('Date frames')
        indexes = [
            models.Index(fields=['start', 'end'], condition=Q(start__isnull=False) & Q(end__isnull=False),
                         name='start_end_idx')
        ]

    def clean(self):
        additional_validators = [
            self.check_start_greater_than_end,
            self.check_task_is_already_completed,
            self.check_start_end_values,
            self.check_pomodoro_duration_fits_error_margin
        ]

        for validator_method in additional_validators:
            validator_method()

        self.duration = self.normalized_duration()

    def normalized_duration(self) -> timedelta:
        date_frame_length = self.normalized_date_frame_length

        if date_frame_length:
            duration_difference = self.duration - date_frame_length

            if timedelta(milliseconds=1) < duration_difference < settings.DATE_FRAME_ERROR_MARGIN:
                truncated_minutes = math.trunc(date_frame_length.seconds / 60)
                return timedelta(minutes=truncated_minutes)
        return self.duration

    def check_start_greater_than_end(self):
        if self.start and self.end and self.start >= self.end:
            raise DFE({'start': DFE.messages[DFE.start_greater_than_end]}, code=DFE.start_greater_than_end)

    def check_task_is_already_completed(self):
        if self.task.status == self.task.status_completed:
            raise DFE({'__all__': DFE.messages[DFE.task_already_completed]}, code=DFE.task_already_completed)

    def check_start_end_values(self):
        started_date_frames_constraint = Q(start__isnull=False) & Q(end__isnull=True)
        finished_date_frames_constraint = Q(start__isnull=False) & Q(end__isnull=False)
        start_constraint, end_constraint = (Q(start__gt=self.start), Q(end__gt=self.start))

        overlapping_task_events = self.selector_class.get_all_date_frames_for_task(
            task=self.task).filter(
            (started_date_frames_constraint | finished_date_frames_constraint) &
            (start_constraint | end_constraint)
        )

        if self.end is not None:
            start_constraint, end_constraint = (Q(start__gt=self.end), Q(end__gt=self.end))
            overlapping_task_events = overlapping_task_events.filter(
                start_constraint | end_constraint
            )

        if overlapping_task_events.exists():
            raise DFE({'__all__': DFE.messages[DFE.overlapping_pomodoro]}, code=DFE.overlapping_pomodoro)

    def check_pomodoro_duration_fits_error_margin(self):
        if not self._state.adding:
            duration_difference = self.duration - self.normalized_date_frame_length
            if self.type == self.pomodoro_type:
                if duration_difference > settings.DATE_FRAME_ERROR_MARGIN:
                    raise DFE([DFE.messages[DFE.invalid_pomodoro_length]], code=DFE.invalid_pomodoro_length)

            elif self.type == self.break_type:
                if duration_difference > settings.DATE_FRAME_ERROR_MARGIN:
                    raise DFE([DFE.messages[DFE.invalid_break_length]], code=DFE.invalid_break_length)

    @property
    def normalized_date_frame_length(self):
        if self.type == self.pomodoro_type:
            return self.task.normalized_pomodoro_length
        elif self.type == self.break_type:
            return self.task.normalized_break_length


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
