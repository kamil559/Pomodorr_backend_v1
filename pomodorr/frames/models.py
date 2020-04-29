import uuid
from collections import defaultdict

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeFramedModel, TimeStampedModel


class TaskEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    start = models.DateTimeField(_('start'), blank=False, null=False, default=timezone.now)
    end = models.DateTimeField(_('end'), blank=True, null=True, default=None)
    created_at = models.DateTimeField(_('created at'), default=timezone.now, editable=False)
    duration = models.DurationField(blank=True, null=True, default=None)

    task = models.ForeignKey(to='projects.Task', null=False, blank=False, on_delete=models.CASCADE,
                             related_name='events')

    def __str__(self):
        return f'{self.task.name}'

    class Meta:
        ordering = ('created_at',)
        verbose_name_plural = _('TaskEvents')

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.full_clean()
        super(TaskEvent, self).save(force_insert=False, force_update=False, using=None, update_fields=None)

    def clean(self):
        self.clean_fields()

        errors_mapping = defaultdict(list)

        if self.start and self.end and self.start >= self.end:
            msg = _('Start date of the pomodoro period cannot be greater than or equal the end date.')
            errors_mapping['start'].append(msg)

        if errors_mapping:
            raise ValidationError(errors_mapping)


class Gap(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    start = models.DateTimeField(_('start'), blank=False, null=False, default=timezone.now)
    end = models.DateTimeField(_('end'), blank=True, null=True, default=None)
    created_at = models.DateTimeField(_('created at'), default=timezone.now, editable=False)

    task_event = models.ForeignKey(to='frames.TaskEvent', null=False, blank=False, on_delete=models.CASCADE,
                                   related_name='gaps')

    class Meta:
        ordering = ('created_at',)
        verbose_name_plural = _('Gaps')

# class DateFrame(TimeStampedModel):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     start = models.DateTimeField(_('start'), blank=False, null=False, default=timezone.now)
#     end = models.DateTimeField(_('end'), blank=True, null=True, default=None)
#     duration = models.DurationField(blank=True, null=True, default=None)
#     TYPE_CHOICES = Choices(
#         (0, 'pomodor'),
#         (1, 'break'),
#         (2, 'pause')
#     )
#     type = StatusField(blank=False, null=False, choices_name=TYPE_CHOICES)
#     task = models.ForeignKey(to='projects.Task', null=False, blank=False, on_delete=models.CASCADE,
#                              related_name='frames')
#
#     def __str__(self):
#         return f'{self.task.name}'
#
#     class Meta:
#         ordering = ('created_at',)
#         verbose_name_plural = _('TaskEvents')
#         indexes = [
#             models.Index(fields=['start', 'end'], condition=Q(start__isnull=False) & Q(end__isnull=False),
#                          name='start_end_idx')
#         ]
#
#     def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
#         self.full_clean()
#         super(DateFrame, self).save(force_insert=False, force_update=False, using=None, update_fields=None)
#
#     def clean(self):
#         self.clean_fields()
#
#         errors_mapping = defaultdict(list)
#
#         if self.start and self.end and self.start >= self.end:
#             msg = _('Start date of the pomodoro period cannot be greater than or equal the end date.')
#             errors_mapping['start'].append(msg)
#
#         if errors_mapping:
#             raise ValidationError(errors_mapping)
