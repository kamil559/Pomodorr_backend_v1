import pytest
from django.utils import timezone
from django.utils.http import urlencode

pytestmark = pytest.mark.django_db


class TestDateFrameViewSetQueries:
    base_url = '/api/date_frames/'

    def test_date_frame_list_view(self, client, django_assert_num_queries, active_user, date_frame_create_batch):
        client.force_authenticate(user=active_user)
        with django_assert_num_queries(2):
            client.get(self.base_url)

    @pytest.mark.parametrize(
        'filter_lookup',
        [
            {'created': timezone.now()},
            {'created__gt': timezone.now()},
            {'created__gte': timezone.now()},
            {'created__lt': timezone.now()},
            {'created__lte': timezone.now()},
            {'frame_type': 0},
            {'frame_type': 1},
            {'frame_type': 2},
            {'is_finished': True},
            {'is_finished': 1},
            {'is_finished': False},
            {'is_finished': 0},
        ]
    )
    def test_date_frame_list_view_filter(self, filter_lookup, client, django_assert_max_num_queries, active_user,
                                         date_frame_create_batch):
        url = f'{self.base_url}?{urlencode(query=filter_lookup)}'
        client.force_authenticate(user=active_user)
        with django_assert_max_num_queries(2):
            client.get(url)
