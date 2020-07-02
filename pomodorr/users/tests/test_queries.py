import pytest
from django.urls import reverse

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


def test_user_list_view(client, active_user, active_user_batch, django_assert_num_queries):
    with django_assert_num_queries(2):  # Initial query will contain a subquery executed for the annotated field
        client.force_authenticate(user=active_user)
        client.get(reverse('api:user-list'))
