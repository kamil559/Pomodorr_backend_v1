from datetime import timedelta

from django.contrib.sites.models import Site
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode


def get_time_delta(time_constraint, ahead=True):
    if ahead:
        return timezone.now() + timedelta(**time_constraint)
    return timezone.now() - timedelta(**time_constraint)


def get_default_domain():
    return Site.objects.get_current().domain


def reverse_query_params(view, urlconf=None, args=None, kwargs=None, current_app=None, query_kwargs=None):
    base_url = reverse(view, urlconf=urlconf, args=args, kwargs=kwargs, current_app=current_app)
    if query_kwargs:
        return f'{base_url}?{urlencode(query_kwargs)}'
    return base_url
