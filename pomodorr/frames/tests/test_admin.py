import pytest

pytestmark = pytest.mark.django_db


class TestDateFrameAdmin:
    def test_is_finished_filter_lookup_choices(self, is_finished_filter):
        is_finished_lookup_choices = is_finished_filter.lookup_choices
        assert is_finished_lookup_choices == [('1', 'Yes'), ('0', 'No')]

    def test_is_finished_filter_get_non_finished_date_frames(self, is_finished_filter, date_frame_admin_queryset,
                                                             date_frame_create_batch, date_frame_in_progress,
                                                             request_mock):
        is_finished_filter.used_parameters['is_finished'] = '0'
        non_finished_date_frames_results = is_finished_filter.queryset(request=request_mock,
                                                                       queryset=date_frame_admin_queryset)

        assert non_finished_date_frames_results.count() == 1
        assert date_frame_in_progress in non_finished_date_frames_results
        assert all(date_frame not in non_finished_date_frames_results for date_frame in date_frame_create_batch)

    def test_is_finished_filter_get_finished_date_frames(self, is_finished_filter, date_frame_admin_queryset,
                                                         date_frame_create_batch, date_frame_in_progress,
                                                         request_mock):
        is_finished_filter.used_parameters['is_finished'] = '1'
        non_finished_date_frames_results = is_finished_filter.queryset(request=request_mock,
                                                                       queryset=date_frame_admin_queryset)

        assert non_finished_date_frames_results.count() == 5
        assert date_frame_in_progress not in non_finished_date_frames_results
        assert all(date_frame in non_finished_date_frames_results for date_frame in date_frame_create_batch)

    def test_is_finished_filter_get_queryset_with_invalid_lookup(self, is_finished_filter, date_frame_admin_queryset,
                                                                 date_frame_create_batch, date_frame_in_progress,
                                                                 request_mock):
        is_finished_filter.used_parameters['is_finished'] = '3'
        non_finished_date_frames_results = is_finished_filter.queryset(request=request_mock,
                                                                       queryset=date_frame_admin_queryset)

        assert non_finished_date_frames_results.count() == 6
        assert date_frame_in_progress in non_finished_date_frames_results
        assert all(date_frame in non_finished_date_frames_results for date_frame in date_frame_create_batch)
