import operator
from datetime import timedelta
from functools import reduce
from unittest.mock import patch
from uuid import uuid4

import pytest
from pytest_lazyfixture import lazy_fixture

from pomodorr.frames.exceptions import DateFrameException
from pomodorr.projects.exceptions import TaskException
from pomodorr.tools.utils import get_time_delta

pytestmark = pytest.mark.django_db()


class TestDateFrameService:
    @patch('pomodorr.frames.services.timezone')
    def test_start_pomodoro_with_valid_start_datetime_within_task(self, mock_timezone, task_event_service_model,
                                                                  task_instance, task_event_instance):
        mock_timezone.now.return_value = get_time_delta({'minutes': 60})

        task_event = task_event_service_model.start_date_frame(task=task_instance)

        assert task_event is not None
        assert task_event.start is not None and task_event.end is None

    @patch('pomodorr.frames.services.timezone')
    def test_check_datetime_available_considers_only_today(self, mock_timezone, task_event_service_model, task_instance,
                                                           task_event_create_batch, task_event_in_progress):
        mock_timezone.now.return_value = (get_time_delta({'days': 1}))
        task_event = task_event_service_model.start_date_frame(task=task_instance)

        assert task_event is not None
        assert task_event.start is not None and task_event.end is None

    @pytest.mark.parametrize(
        'mock_timezone_return_value, expected_exception',
        [
            (get_time_delta({'minutes': 10}, ahead=True), DateFrameException),
            (get_time_delta({'minutes': 60}, ahead=False), DateFrameException)
        ]
    )
    @patch('pomodorr.frames.services.timezone')
    def test_start_pomodoro_with_overlapping_start_datetime_within_task(self, mock_timezone,
                                                                        mock_timezone_return_value,
                                                                        expected_exception,
                                                                        task_event_service_model, task_instance,
                                                                        task_event_create_batch,
                                                                        task_event_in_progress):
        mock_timezone.now.return_value = mock_timezone_return_value

        with pytest.raises(expected_exception) as exc:
            task_event_service_model.start_date_frame(task=task_instance)

        assert exc.value.code == DateFrameException.overlapping_pomodoro

    @patch('pomodorr.frames.services.cache')
    def test_start_pomodoro_with_already_existing_current_pomodoro(self, mock_cache, task_event_service_model,
                                                                   task_instance, task_event_in_progress):
        mock_cache.get.return_value = uuid4()

        with pytest.raises(DateFrameException) as exc:
            task_event_service_model.start_date_frame(task=task_instance)

        assert exc.value.code == DateFrameException.current_pomodoro_exists

    def test_start_pomodoro_for_already_completed_task(self, task_event_service_model, completed_task_instance):
        with pytest.raises(TaskException) as exc:
            task_event_service_model.start_date_frame(task=completed_task_instance)
        assert exc.value.code == TaskException.already_completed

    def test_finish_task_event_with_valid_end_datetime_within_task(self, task_event_service_model, task_instance,
                                                                   task_event_in_progress):
        task_event_service_model.finish_date_frame(task_event=task_event_in_progress)

        assert task_event_in_progress.start < task_event_in_progress.end
        assert task_event_in_progress.end is not None

    @pytest.mark.parametrize(
        'mock_timezone_return_value, expected_exception',
        [
            (get_time_delta({'minutes': 10}, ahead=True), DateFrameException),
            (get_time_delta({'minutes': 60}, ahead=False), DateFrameException)
        ]
    )
    @patch('pomodorr.frames.services.timezone')
    def test_finish_task_event_with_overlapping_end_datetime_within_task(self, mock_timezone,
                                                                         mock_timezone_return_value,
                                                                         expected_exception, task_event_service_model,
                                                                         task_instance, task_event_create_batch,
                                                                         task_event_in_progress):
        mock_timezone.now.return_value = mock_timezone_return_value

        with pytest.raises(expected_exception) as exc:
            task_event_service_model.finish_date_frame(task_event=task_event_in_progress)

        assert exc.value.code == DateFrameException.overlapping_pomodoro

    @patch('pomodorr.frames.services.timezone')
    def test_finish_task_event_with_too_long_pomodoro_duration(self, mock_timezone, task_event_service_model,
                                                               task_event_in_progress):
        mock_timezone.now.return_value = get_time_delta({'minutes': 30})

        with pytest.raises(DateFrameException) as exc:
            task_event_service_model.finish_date_frame(task_event=task_event_in_progress)

        assert exc.value.code == DateFrameException.invalid_pomodoro_length

    @patch('pomodorr.frames.services.timezone')
    def test_finish_pomodoro_with_gaps(self, mock_timezone, task_event_service_model, task_event_in_progress_with_gaps):
        gaps_duration = reduce(operator.add,
                               (gap.end - gap.start for gap in task_event_in_progress_with_gaps.gaps.all()))
        expected_duration = timedelta(minutes=25)

        mock_timezone.now.return_value = get_time_delta({'minutes': 25}) + gaps_duration

        task_event_service_model.finish_date_frame(task_event=task_event_in_progress_with_gaps)

        assert task_event_in_progress_with_gaps.end is not None
        assert task_event_in_progress_with_gaps.duration == expected_duration

    def test_finish_pomodoro_for_already_completed_task(self, task_event_service_model, completed_task_instance,
                                                        task_event_in_progress):
        task_event_in_progress.task = completed_task_instance
        task_event_in_progress.save()

        with pytest.raises(TaskException) as exc:
            task_event_service_model.finish_date_frame(task_event=task_event_in_progress)
        assert exc.value.code == TaskException.already_completed

    @pytest.mark.parametrize(
        'start_date, end_date, excluded_task_event, expected_exception',
        [
            (get_time_delta({'minutes': 10}, ahead=True), None, None, DateFrameException),
            (get_time_delta({'minutes': 10}, ahead=False), None, None, DateFrameException),
            (get_time_delta({'minutes': 10}, ahead=True), get_time_delta({'minutes': 10}, ahead=True),
             lazy_fixture('task_event_instance'), DateFrameException),
            (get_time_delta({'minutes': 10}, ahead=False), get_time_delta({'minutes': 10}, ahead=True),
             lazy_fixture('task_event_instance'), DateFrameException)
        ]
    )
    def test_check_start_datetime_available(self, start_date, end_date, excluded_task_event, expected_exception,
                                            task_event_service_model, task_instance, task_event_create_batch,
                                            task_event_instance):
        with pytest.raises(expected_exception) as exc:
            task_event_service_model.check_datetime_available(task=task_instance, start_date=start_date,
                                                              end_date=end_date,
                                                              excluded_task_event=excluded_task_event)

        assert exc.value.code == DateFrameException.overlapping_pomodoro

    def test_get_task_event_duration_with_valid_finish_datetime(self, task_event_service_model, task_event_in_progress):
        finish_date_within_error_margin = task_event_in_progress.start + timedelta(minutes=25, seconds=59)

        task_event_duration = task_event_service_model.get_task_event_duration(
            task_event=task_event_in_progress, finish_datetime=finish_date_within_error_margin)

        assert task_event_duration == timedelta(minutes=25)

    def test_get_task_event_duration_with_shorter_duration(self, task_event_service_model, task_event_in_progress):
        finish_date_within_error_margin = task_event_in_progress.start + timedelta(minutes=5)

        task_event_duration = task_event_service_model.get_task_event_duration(
            task_event=task_event_in_progress, finish_datetime=finish_date_within_error_margin)

        assert task_event_duration == timedelta(minutes=5)

    def test_normalize_pomodoro_duration_with_valid_duration(self, task_event_service_model, task_event_in_progress):
        task_event_duration = timedelta(minutes=25, seconds=59)
        expected_normalized_duration = timedelta(minutes=25)

        normalized_duration = task_event_service_model.normalize_pomodoro_duration(
            task_event_duration=task_event_duration,
            task_event=task_event_in_progress,
            error_margin={'minutes': 1})

        assert normalized_duration == expected_normalized_duration

    def test_normalize_pomodoro_duration_with_shorter_duration(self, task_event_service_model, task_event_in_progress):
        task_event_duration = timedelta(minutes=5, seconds=10, milliseconds=12)
        expected_normalized_duration = task_event_duration

        normalized_duration = task_event_service_model.normalize_pomodoro_duration(
            task_event_duration=task_event_duration,
            task_event=task_event_in_progress,
            error_margin={'minutes': 1})

        assert normalized_duration == expected_normalized_duration

    def test_normalize_pomodoro_duration_with_too_long_duration(self, task_event_service_model, task_event_in_progress):
        task_event_duration = timedelta(minutes=26, microseconds=1)

        with pytest.raises(DateFrameException) as exc:
            task_event_service_model.normalize_pomodoro_duration(
                task_event_duration=task_event_duration,
                task_event=task_event_in_progress,
                error_margin={'minutes': 1})

        assert exc.value.code == DateFrameException.invalid_pomodoro_length

    @pytest.mark.xfail
    def test_get_pomodoro_length(self, task_event_service_model, task_instance):
        pomodoro_length = task_event_service_model.get_pomodoro_length(task=task_instance)

        assert pomodoro_length == task_instance.normalized_pomodoro_length

    @patch('pomodorr.frames.services.cache')
    def test_check_current_task_event_is_connected(self, mock_cache, task_event_service_model, task_event_in_progress):
        connection_id = uuid4()
        mock_cache.get.return_value = connection_id

        with pytest.raises(DateFrameException) as exc:
            task_event_service_model.check_current_task_event_is_connected(task_event=task_event_in_progress)

        assert exc.value.code == DateFrameException.current_pomodoro_exists

    def test_remove_task_event(self, task_event_service_model, task_event_instance):
        task_event_service_model.remove_task_event(task_event=task_event_instance)

        assert task_event_instance.id is None

    def test_remove_gaps(self, task_event_service_model, task_event_instance_with_unfinished_gaps):
        assert task_event_instance_with_unfinished_gaps.gaps.count() == 2

        task_event_service_model.remove_gaps(task_event=task_event_instance_with_unfinished_gaps)

        assert task_event_instance_with_unfinished_gaps.gaps.count() == 0
