from datetime import timedelta

from django.contrib.sites.models import Site
from django.utils import timezone


def get_time_delta(**time_constraint):
    return timezone.now() + timedelta(**time_constraint)


def get_default_domain():
    return Site.objects.get_current().domain
