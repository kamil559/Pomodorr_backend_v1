import uuid

from django.db import models
from colorfield.fields import ColorField
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from model_utils.models import SoftDeletableModel


class CustomProfileQueryset(models.QuerySet):
    def delete(self, soft=True):
        if soft:
            self.update(is_removed=True)
        else:
            super(CustomProfileQueryset, self).delete()


class CustomProfileManagerMixin:
    _queryset_class = CustomProfileQueryset


class CustomProfileManager(CustomProfileManagerMixin, models.Manager):
    pass


class Project(SoftDeletableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(null=False, blank=False, max_length=128)
    color = ColorField(default='#FF0000')
    priority = models.PositiveIntegerField(blank=False, null=False, default=1)
    user_defined_ordering = models.PositiveIntegerField(blank=False, null=False, default=1)
    user = models.ForeignKey(to='users.User', null=False, blank=False, on_delete=models.CASCADE,
                             related_name='projects')
    created_at = models.DateTimeField(_('created at'), default=timezone.now, editable=False)

    all_objects = CustomProfileManager()

    class Meta:
        unique_together = ['name', 'user']
        ordering = ('created_at', 'priority', 'user_defined_ordering')

    def __str__(self):
        return f'{self.name}'
