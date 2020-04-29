import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Gap(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    start = models.DateTimeField(_('start'), blank=False, null=False, default=timezone.now)
    end = models.DateTimeField(_('end'), blank=True, null=True, default=None)
    created_at = models.DateTimeField(_('created at'), default=timezone.now, editable=False)

    task_event = models.ForeignKey(to='projects.TaskEvent', null=False, blank=False, on_delete=models.CASCADE,
                                   related_name='gaps')

    class Meta:
        ordering = ('created_at',)
        verbose_name_plural = _('Gaps')
