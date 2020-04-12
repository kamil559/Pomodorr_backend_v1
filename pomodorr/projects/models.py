from django.db import models
from colorfield.fields import ColorField


class Project(models.Model):
    name = models.CharField(null=False, blank=False, max_length=128)
    color = ColorField(default='#FF0000')
    priority = models.PositiveIntegerField()
    user_defined_ordering = models.PositiveIntegerField()
    user = models.ForeignKey(to='users.User', null=False, blank=False, on_delete=models.CASCADE,
                             related_name='projects')

    class Meta:
        unique_together = ['name', 'user']

    def __str__(self):
        return f'{self.name}'
