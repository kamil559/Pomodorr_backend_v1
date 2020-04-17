import uuid
from collections import defaultdict

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
    priority_level = models.PositiveIntegerField(null=False, default=1)
    color = ColorField(default='#FF0000')
    user = models.ForeignKey(to='users.User', blank=False, null=False, on_delete=models.CASCADE,
                             related_name='priorities')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'user'], name='unique_user_priority')
        ]
        ordering = ('-priority_level',)
        verbose_name_plural = _('Priorities')

    def __str__(self):
        return f'{self.priority_level} - {self.name}'


class Project(SoftDeletableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(null=False, blank=False, max_length=128)
    priority = models.ForeignKey(to='projects.Priority', blank=True, null=True, on_delete=models.CASCADE,
                                 related_name='projects')
    user_defined_ordering = models.PositiveIntegerField(null=False, default=0)
    user = models.ForeignKey(to='users.User', blank=False, null=False, on_delete=models.CASCADE,
                             related_name='projects')
    created_at = models.DateTimeField(_('created at'), default=timezone.now, editable=False)

    all_objects = CustomSoftDeletableManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'user'], name='unique_user_project', condition=Q(is_removed=False))
        ]
        ordering = ('created_at', 'user_defined_ordering', '-priority__priority_level')
        verbose_name_plural = _('Projects')

    def __str__(self):
        return f'{self.name}'


class Task(SoftDeletableModel):
    STATUS_CHOICES = [
        (0, _('active')),
        (1, _('completed'))
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(blank=False, null=False, max_length=128)
    status = models.PositiveIntegerField(null=False, choices=STATUS_CHOICES, default=0)
    priority = models.ForeignKey(to='projects.Priority', blank=True, null=True, on_delete=models.CASCADE,
                                 related_name='tasks')
    user_defined_ordering = models.PositiveIntegerField(null=False, default=0)
    pomodoro_number = models.PositiveIntegerField(null=False, default=0)
    due_date = models.DateField(blank=True, null=True, default=None)
    reminder_date = models.DateTimeField(blank=True, null=True, default=None)
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
        indexes = [
            models.Index(fields=['status'], name='index_status_active', condition=Q(status=0))
        ]
        ordering = ('created_at', 'user_defined_ordering', '-priority__priority_level')
        verbose_name_plural = _('Tasks')

    def __str__(self):
        return f'{self.name}'

    # todo: add validation for repeat_duration (acceptable None, min value 1 day)


class SubTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(blank=False, null=False, max_length=128)
    task = models.ForeignKey(to='projects.Task', null=False, blank=False, on_delete=models.CASCADE,
                             related_name='sub_tasks')
    created_at = models.DateTimeField(_('created at'), default=timezone.now, editable=False)
    is_completed = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'task'], name='unique_sub_task')
        ]
        ordering = ('created_at',)
        verbose_name_plural = _('SubTasks')

    def __str__(self):
        return f'{self.name}'


class TaskEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    start = models.DateTimeField(_('start'), blank=False, null=False)
    end = models.DateTimeField(_('end'), blank=False, null=False)
    created_at = models.DateTimeField(_('created at'), default=timezone.now, editable=False)

    task = models.ForeignKey(to='projects.Task', null=False, blank=False, on_delete=models.CASCADE,
                             related_name='events')

    def __str__(self):
        return f'{self.task.name}'

    class Meta:
        ordering = ('created_at',)
        verbose_name_plural = _('TaskEvents')
        # todo: check query time without and with different types of indexes (simple index and index together)

    def clean(self):
        errors_mapping = defaultdict(list)

        if self.start >= self.end:
            msg = _('Start date of the pomodoro period cannot be greater than or equal the end date.')
            errors_mapping['start'].append(msg)

        # todo: will be done after creating the user's setting module
        # user = self.task.project.user
        # start_end_difference: timedelta = end - start
        # if start_end_difference < user.settings.pomodoro_duration:
        #     msg = _('The pomodoro period has not been finished yet.')
        #     errors_mapping['non_field_errors'].append(msg)

        if errors_mapping:
            raise ValidationError(errors_mapping)
