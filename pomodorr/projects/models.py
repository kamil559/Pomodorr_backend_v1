import uuid
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from colorfield.fields import ColorField
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from model_utils.models import SoftDeletableModel, TimeFramedModel


class CustomSoftDeletableQueryset(models.QuerySet):
    def delete(self, soft=True):
        if soft:
            self.update(is_removed=True)
        else:
            super(CustomSoftDeletableQueryset, self).delete()


class CustomManagerMixin:
    _queryset_class = CustomSoftDeletableQueryset


class CustomSoftDeletableManager(CustomManagerMixin, models.Manager):
    pass


class Priority(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(blank=False, null=False, max_length=128)
    priority = models.PositiveIntegerField(blank=False, null=False, default=1)
    user = models.ForeignKey(to='users.User', blank=False, null=False, on_delete=models.CASCADE,
                             related_name='priorities')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['priority', 'user'], name='unique_user_priority_level')
        ]


class Project(SoftDeletableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(null=False, blank=False, max_length=128)
    color = ColorField(default='#FF0000')
    priority = models.ForeignKey(to='projects.Priority', blank=True, null=True, on_delete=models.CASCADE,
                                 related_name='projects')
    user_defined_ordering = models.PositiveIntegerField(blank=False, null=False, default=0)
    user = models.ForeignKey(to='users.User', blank=False, null=False, on_delete=models.CASCADE,
                             related_name='projects')
    created_at = models.DateTimeField(_('created at'), default=timezone.now, editable=False)

    all_objects = CustomSoftDeletableManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'user'], name='unique_user_project', condition=Q(is_removed=False))
        ]
        ordering = ('created_at', 'user_defined_ordering', '-priority')

    def __str__(self):
        return f'{self.name}'


class Task(SoftDeletableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(blank=False, null=False, max_length=128)
    color = ColorField(default='#FF0000')
    priority = models.ForeignKey(to='projects.Priority', blank=True, null=True, on_delete=models.CASCADE,
                                 related_name='tasks')
    user_defined_ordering = models.PositiveIntegerField(blank=False, null=False, default=0)
    pomodoro_number = models.PositiveIntegerField(blank=False, null=False)
    due_date = models.DateField(blank=False, null=False, default=timezone.now)
    reminder_date = models.DateTimeField(blank=True, null=True)
    repeat_duration = models.DurationField(blank=True, null=True, default=None)
    project = models.ForeignKey(to='projects.Project', null=False, blank=False, on_delete=models.CASCADE,
                                related_name='tasks')
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(_('created at'), default=timezone.now, editable=False)

    all_objects = CustomSoftDeletableManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'project'], name='unique_project_task',
                                    condition=Q(is_removed=False))
        ]
        ordering = ('created_at', 'user_defined_ordering', '-priority')

    def __str__(self):
        return f'{self.name}'


class SubTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(blank=False, null=False, max_length=128)
    task = models.ForeignKey(to='projects.Task', null=False, blank=False, on_delete=models.CASCADE,
                             related_name='sub_tasks')
    created_at = models.DateTimeField(_('created at'), default=timezone.now, editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'task'], name='unique_sub_task')
        ]
        ordering = ('created_at',)

    def __str__(self):
        return f'{self.name}'


class TaskEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    start = models.DateTimeField(_('start'), blank=False, null=True)
    end = models.DateTimeField(_('end'), blank=False, null=True)
    created_at = models.DateTimeField(_('created at'), default=timezone.now, editable=False)

    task = models.ForeignKey(to='projects.Task', null=False, blank=False, on_delete=models.CASCADE,
                             related_name='events')

    def __str__(self):
        return f'{self.task.name} on {self.created_at}'

    class Meta:
        ordering = ('created_at',)
        # todo: check query time without and with different types of indexes (simple index and index together)

    def clean(self):
        start = self.start
        end = self.end

        base_query = self.objects.filter(Q(task=self.task)).prefetch_related('events')

        if start > end:
            msg = _('Start date of the pomodoro period cannot be greater than the end date.')
            raise ValidationError(msg)

        start_end_difference: timedelta = end - start

        if start_end_difference < self.task.repeat_duration:
            msg = _('The pomodoro period has not been finished yet.')
            raise ValidationError(msg)

        if base_query.filter(
            (
                Q(start__date=start.date()) &
                (
                    Q(start__time__gt=start.time()) |
                    Q(end__time__gt=start.time()) |
                    Q(start__time__gt=end.time()) |
                    Q(end__time__gt=end.time())
                )
            )
        ).exists():
            msg = _('There is a collision between this pomodoro period and some previous pomodoros.')
            raise ValidationError(msg)
