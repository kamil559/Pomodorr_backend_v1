import uuid
from datetime import timedelta
from typing import Union

from colorfield.fields import ColorField
from django.db import models
from django.db.models import Q, DurationField
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
    color = ColorField(blank=True, default='#FF0000')
    user = models.ForeignKey(to='users.User', blank=False, null=False, on_delete=models.CASCADE,
                             related_name='priorities')
    created_at = models.DateTimeField(_('created at'), default=timezone.now, editable=False)

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
    priority = models.ForeignKey(to='projects.Priority', blank=True, null=True, on_delete=models.SET_NULL,
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
    status_active = 0
    status_completed = 1

    STATUS_CHOICES = [
        (status_active, _('active')),
        (status_completed, _('completed'))
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(blank=False, null=False, max_length=128)
    status = models.PositiveIntegerField(blank=False, null=False, choices=STATUS_CHOICES, default=0)
    priority = models.ForeignKey(to='projects.Priority', blank=True, null=True, on_delete=models.SET_NULL,
                                 related_name='tasks')
    user_defined_ordering = models.PositiveIntegerField(null=False, default=0)
    pomodoro_number = models.PositiveIntegerField(blank=True, null=True, default=0)
    pomodoro_length = models.DurationField(blank=True, null=True, default=None)
    break_length = models.DurationField(blank=True, null=True, default=None)
    due_date = models.DateTimeField(blank=True, null=True, default=None)
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
                                    condition=Q(is_removed=False) & Q(status=0))
        ]
        indexes = [
            models.Index(fields=['status'], name='index_status_active', condition=Q(status=0))
        ]
        ordering = ('created_at', 'user_defined_ordering', '-priority__priority_level')
        verbose_name_plural = _('Tasks')

    def __str__(self):
        return f'{self.name}'

    @property
    def normalized_pomodoro_length(self) -> Union[None, timedelta, DurationField]:
        # todo: will be applied once the user settings module has been implemented
        # user_settings = self.project.user
        # global_pomodoro_length = user_settings.pomodoro_length
        if self.pomodoro_length is not None:
            return self.pomodoro_length
        # return global_pomodoro_length

    @property
    def normalized_break_length(self) -> Union[None, timedelta, DurationField]:
        # todo: will be applied once the user settings module has been implemented
        # user_settings = self.project.user
        # global_break_length = user_settings.break_length
        if self.break_length is not None:
            return self.break_length
        # return global_break_length


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
        ordering = ('created_at', 'name', 'is_completed')
        verbose_name_plural = _('SubTasks')

    def __str__(self):
        return f'{self.name}'
