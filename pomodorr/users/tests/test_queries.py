import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestUsersModelManagerQueries:
    def test_get_queryset(self, user_model, django_assert_num_queries):
        with django_assert_num_queries(1):
            repr(user_model.objects.all())

    def test_get_active_standard_users(self, user_model, django_assert_num_queries):
        with django_assert_num_queries(1):
            repr(user_model.objects.active_standard_users())

    def test_get_non_active_standard_users(self, user_model, django_assert_num_queries):
        with django_assert_num_queries(1):
            repr(user_model.objects.non_active_standard_users())

    def test_get_blocked_standard_users(self, user_model, django_assert_num_queries):
        with django_assert_num_queries(1):
            repr(user_model.objects.blocked_standard_users())

    def test_get_ready_to_unblock_users(self, user_model, django_assert_num_queries):
        with django_assert_num_queries(1):
            repr(user_model.objects.ready_to_unblock_users())


# class TestUsersAPIQueries:
#     def test_user_list_view(self, client, django_assert_num_queries):
#         with django_assert_num_queries(1):
#             response = client.get(reverse('users-list'))
#         print()
#
#     def test_user_detail_view(self, client, django_assert_num_queries):
#         with django_assert_num_queries(1):
#             response = client.get(reverse('users-me'))

