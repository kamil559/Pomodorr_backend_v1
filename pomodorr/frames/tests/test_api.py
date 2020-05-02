import pytest
from django.utils import timezone
from django.utils.http import urlencode
from rest_framework import status
from rest_framework.test import force_authenticate

from pomodorr.frames.api import DateFrameListView
from pomodorr.frames.models import DateFrame
from pomodorr.frames.selectors import DateFrameSelector

pytestmark = pytest.mark.django_db


class TestDateFrameListView:
    view_class = DateFrameListView
    selector_class = DateFrameSelector(model_class=DateFrame)
    base_url = 'api/date_frames'

    def test_get_date_frame_list(self, date_frame_create_batch, date_frame_for_random_task, active_user,
                                 request_factory):
        view = self.view_class.as_view({'get': 'list'})
        request = request_factory.get(self.base_url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None
        assert response.data['count'] == 5

    @pytest.mark.parametrize(
        'ordering',
        ['created', '-created', 'duration', '-duration', 'is_finished', '-is_finished']
    )
    def test_get_date_frame_list_ordered_by_valid_fields(self, ordering, date_frame_create_batch, active_user,
                                                         request_factory):
        view = self.view_class.as_view({'get': 'list'})
        url = f'{self.base_url}?{urlencode(query={"ordering": ordering})}'
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None

        response_result_ids = [record['id'] for record in response.data['results']]
        sorted_orm_fetched_date_frames = list(map(
            lambda uuid: str(uuid), self.selector_class.get_all_date_frames_for_user(
                user=active_user).order_by(ordering).values_list('id', flat=True)))

        assert response_result_ids == sorted_orm_fetched_date_frames

    @pytest.mark.parametrize(
        'ordering',
        ['task__project__user__password', 'task__project__user__is_superuser']
    )
    def test_get_date_frame_fields_ordered_by_invalid_fields(self, ordering, date_frame_create_batch, active_user,
                                                             request_factory):
        view = self.view_class.as_view({'get': 'list'})
        url = f'{self.base_url}?{urlencode(query={"ordering": ordering})}'
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None

        response_result_ids = [record['id'] for record in response.data['results']]
        default_sorted_orm_fetched_date_frames = list(map(
            lambda uuid: str(uuid), self.selector_class.get_all_date_frames_for_user(
                user=active_user).values_list('id', flat=True)))
        assert response_result_ids == default_sorted_orm_fetched_date_frames

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
    def test_get_filtered_date_frame_fields(self, filter_lookup, date_frame_create_batch,
                                            date_frame_in_progress_for_yesterday, date_frame_instance, active_user,
                                            request_factory):
        view = self.view_class.as_view({'get': 'list'})
        url = f'{self.base_url}?{urlencode(query=filter_lookup)}'
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None

        response_result_ids = [record['id'] for record in response.data['results']]
        default_filtered_orm_fetched_data_frames = list(map(
            lambda uuid: str(uuid), self.selector_class.get_all_date_frames_for_user(
                user=active_user).filter(**filter_lookup).values_list('id', flat=True)
        ))

        assert response_result_ids == default_filtered_orm_fetched_data_frames
