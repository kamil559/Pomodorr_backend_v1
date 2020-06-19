from datetime import timedelta, datetime

from django.contrib.sites.models import Site
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode


def get_time_delta(time_constraint: dict, ahead=True) -> datetime:
    if ahead:
        return timezone.now() + timedelta(**time_constraint)
    return timezone.now() - timedelta(**time_constraint)


def get_default_domain() -> str:
    return Site.objects.get_current().domain


def reverse_query_params(view, urlconf=None, args=None, kwargs=None, current_app=None, query_kwargs=None) -> str:
    base_url = reverse(view, urlconf=urlconf, args=args, kwargs=kwargs, current_app=current_app)
    if query_kwargs:
        return f'{base_url}?{urlencode(query_kwargs)}'
    return base_url


def has_changed(instance, key, value, check_value=None) -> bool:
    changed = getattr(instance, key) != value
    if check_value is not None:
        return changed and value == check_value
    return changed
