import pytest
from django.contrib.auth import get_user_model

User = get_user_model()
pytestmark = pytest.mark.django_db


def test_get_queryset(django_assert_num_queries):
    with django_assert_num_queries(1):
        repr(User.objects.all())


def test_get_active_standard_users(django_assert_num_queries):
    with django_assert_num_queries(1):
        repr(User.objects.active_standard_users())


def test_get_non_active_standard_users(django_assert_num_queries):
    with django_assert_num_queries(1):
        repr(User.objects.non_active_standard_users())


def test_get_blocked_standard_users(django_assert_num_queries):
    with django_assert_num_queries(1):
        repr(User.objects.blocked_standard_users())


def test_get_ready_to_unblock_users(django_assert_num_queries):
    with django_assert_num_queries(1):
        repr(User.objects.ready_to_unblock_users())
