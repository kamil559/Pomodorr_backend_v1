import pytest

pytestmark = pytest.mark.django_db


def test_is_blocked_filter_lookup_choices(is_blocked_filter):
    is_blocked_lookup_choices = is_blocked_filter.lookup_choices

    assert is_blocked_lookup_choices == [('1', 'Yes'), ('0', 'No')]


def test_is_blocked_filter_get_non_blocked_users(request_mock, is_blocked_filter, user_admin_queryset, admin_user,
                                                 active_user, blocked_user):
    is_blocked_filter.used_parameters['is_blocked'] = '0'  # Filter for non blocked users
    non_blocked_users_result = is_blocked_filter.queryset(request=request_mock, queryset=user_admin_queryset)

    assert non_blocked_users_result.count() == 2  # Contains admin_user, thus total should be equal 2
    assert blocked_user not in non_blocked_users_result
    assert all([user in non_blocked_users_result] for user in [admin_user, active_user])


def test_is_blocked_filter_get_blocked_users(request_mock, is_blocked_filter, user_admin_queryset, admin_user,
                                             active_user, blocked_user):
    is_blocked_filter.used_parameters['is_blocked'] = '1'  # Filter for blocked users
    non_blocked_users_result = is_blocked_filter.queryset(request=request_mock, queryset=user_admin_queryset)

    assert non_blocked_users_result.count() == 1  # Only the blocked user should be returned
    assert blocked_user in non_blocked_users_result
    assert all([user not in non_blocked_users_result] for user in [admin_user, active_user])


def test_is_blocked_filter_get_queryset_with_invalid_param(request_mock, is_blocked_filter, user_admin_queryset,
                                                           admin_user, active_user, blocked_user):
    is_blocked_filter.used_parameters['is_blocked'] = '3'  # Filter for blocked users
    query_result = is_blocked_filter.queryset(request=request_mock, queryset=user_admin_queryset)

    assert query_result.count() == 3  # Only the blocked user should be returned
    assert blocked_user in query_result
    assert all([user in query_result] for user in [admin_user, active_user, blocked_user])
