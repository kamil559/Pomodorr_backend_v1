from datetime import timedelta

import pytest
from pytest_lazyfixture import lazy_fixture

from pomodorr.frames.selectors.date_frame_selector import (
    get_all_date_frames, get_all_date_frames_for_user, get_all_date_frames_for_project, get_all_date_frames_for_task,
    get_breaks_inside_date_frame, get_pauses_inside_date_frame, get_latest_date_frame_in_progress_for_task,
    get_colliding_date_frame_for_task, get_finished_date_frames_for_user, get_finished_date_frames_for_task,
    get_obsolete_date_frames
)
from pomodorr.tools.utils import get_time_delta

pytestmark = pytest.mark.django_db


class TestDateFrame:
    def test_get_all_date_frames(self, date_frame_in_progress_for_yesterday, date_frame_create_batch,
                                 date_frame_for_random_task):
        selector_method_result = get_all_date_frames()

        assert selector_method_result.count() == 7
        assert date_frame_in_progress_for_yesterday in selector_method_result
        assert date_frame_for_random_task in selector_method_result

    def test_get_finished_date_frames_for_user(self, active_user, pomodoro_in_progress, pause_in_progress,
                                               break_in_progress, date_frame_instance):
        selector_method_result = get_finished_date_frames_for_user(user=active_user.id)

        assert selector_method_result.count() == 1
        assert pomodoro_in_progress not in selector_method_result
        assert pause_in_progress not in selector_method_result
        assert break_in_progress not in selector_method_result

    def test_get_finished_date_frames_for_task(self, task_instance, pomodoro_in_progress, pause_in_progress,
                                               break_in_progress, date_frame_instance):
        selector_method_result = get_finished_date_frames_for_task(task=task_instance)

        assert selector_method_result.count() == 1
        assert pomodoro_in_progress not in selector_method_result
        assert pause_in_progress not in selector_method_result
        assert break_in_progress not in selector_method_result

    def test_get_all_date_frames_for_user(self, date_frame_in_progress_for_yesterday,
                                          date_frame_create_batch, date_frame_for_random_task, active_user):
        selector_method_result = get_all_date_frames_for_user(user=active_user)

        assert selector_method_result.count() == 6
        assert date_frame_for_random_task not in selector_method_result
        assert date_frame_in_progress_for_yesterday in selector_method_result

    def test_get_all_date_frames_for_project(self, date_frame_in_progress_for_yesterday,
                                             date_frame_create_batch, date_frame_create_batch_for_second_project,
                                             date_frame_for_random_task, second_project_instance):
        selector_method_result = get_all_date_frames_for_project(project=second_project_instance)

        assert selector_method_result.count() == 5
        assert date_frame_in_progress_for_yesterday not in selector_method_result
        assert date_frame_for_random_task not in selector_method_result

    def test_get_all_date_frames_for_task(self, date_frame_in_progress_for_yesterday,
                                          date_frame_create_batch, date_frame_create_batch_for_second_project,
                                          task_instance):
        selector_method_result = get_all_date_frames_for_task(task=task_instance)
        assert selector_method_result.count() == 6
        assert date_frame_in_progress_for_yesterday in selector_method_result
        assert all(
            date_frame not in selector_method_result for date_frame in date_frame_create_batch_for_second_project)

    def test_get_breaks_inside_date_frame(self, pomodoro_in_progress_with_breaks):
        finish_date = get_time_delta({'minutes': 25})
        selector_method_result = get_breaks_inside_date_frame(
            date_frame_object=pomodoro_in_progress_with_breaks, end=finish_date)

        assert selector_method_result.count() == 2
        assert all(date_frame.start > pomodoro_in_progress_with_breaks.start for date_frame in selector_method_result)
        assert all(date_frame.end < finish_date for date_frame in selector_method_result)

    def test_get_pauses_inside_date_frame(self, pomodoro_in_progress_with_pauses):
        finish_date = get_time_delta({'minutes': 25})
        selector_method_result = get_pauses_inside_date_frame(
            date_frame_object=pomodoro_in_progress_with_pauses, end=finish_date)

        assert selector_method_result.count() == 2
        assert all(date_frame.start > pomodoro_in_progress_with_pauses.start for date_frame in selector_method_result)
        assert all(date_frame.end < finish_date for date_frame in selector_method_result)

    @pytest.mark.parametrize(
        'tested_date_frame',
        [
            lazy_fixture('pomodoro_in_progress'),
            lazy_fixture('break_in_progress'),
            lazy_fixture('pause_in_progress')
        ]
    )
    def test_get_latest_date_frame_in_progress_for_task(self, tested_date_frame, task_instance,
                                                        date_frame_in_progress_for_yesterday):
        selector_method_result = get_latest_date_frame_in_progress_for_task(task_id=task_instance.id)

        assert selector_method_result == tested_date_frame

    @pytest.mark.parametrize(
        'tested_date_frame, colliding_date_frame',
        [
            (lazy_fixture('pomodoro_in_progress'), lazy_fixture('date_frame_instance')),
            (lazy_fixture('pomodoro_in_progress'), lazy_fixture('date_frame_in_progress')),
            (lazy_fixture('break_in_progress'), lazy_fixture('date_frame_instance')),
            (lazy_fixture('break_in_progress'), lazy_fixture('date_frame_in_progress')),
            (lazy_fixture('pause_in_progress'), lazy_fixture('date_frame_instance')),
            (lazy_fixture('pause_in_progress'), lazy_fixture('date_frame_in_progress'))
        ]
    )
    def test_get_colliding_date_frame_by_start_value(self, tested_date_frame, colliding_date_frame, task_instance):
        selector_method_result = get_colliding_date_frame_for_task(
            task_id=task_instance.id, date=tested_date_frame.start + timedelta(minutes=5))

        assert selector_method_result == colliding_date_frame

    def test_get_obsolete_date_frames(self, date_frame_instance, obsolete_date_frames):
        selector_method_result = get_obsolete_date_frames()

        assert selector_method_result.count() == 3
        assert date_frame_instance not in selector_method_result
