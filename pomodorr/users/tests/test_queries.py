import pytest

pytestmark = pytest.mark.django_db


def test_get_queryset(user_model, django_assert_num_queries):
    with django_assert_num_queries(1):
        repr(user_model.objects.all())


def test_get_active_standard_users(user_model, django_assert_num_queries):
    with django_assert_num_queries(1):
        repr(user_model.objects.active_standard_users())


def test_get_non_active_standard_users(user_model, django_assert_num_queries):
    with django_assert_num_queries(1):
        repr(user_model.objects.non_active_standard_users())


def test_get_blocked_standard_users(user_model, django_assert_num_queries):
    with django_assert_num_queries(1):
        repr(user_model.objects.blocked_standard_users())


def test_get_ready_to_unblock_users(user_model, django_assert_num_queries):
    with django_assert_num_queries(1):
        repr(user_model.objects.ready_to_unblock_users())
