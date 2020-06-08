import math
import operator
from datetime import timedelta
from functools import reduce
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from pytest_lazyfixture import lazy_fixture

from pomodorr.frames.exceptions import DateFrameException
from pomodorr.frames.selectors.date_frame_selector import get_breaks_inside_date_frame, get_pauses_inside_date_frame
from pomodorr.frames.services.date_frame_service import start_date_frame, finish_date_frame, force_finish_date_frame
from pomodorr.tools.utils import get_time_delta

pytestmark = pytest.mark.django_db()


class TestStartDateFrame:

    @pytest.mark.parametrize(
        'date_frame_type',
        [0, 1, 2]
    )
    def test_start_date_frame_with_valid_start_datetime(self, date_frame_type, task_instance):
        assert task_instance.frames.count() == 0
        start_date_frame(task_id=task_instance.id, frame_type=date_frame_type)
        assert task_instance.frames.count() == 1

    @pytest.mark.parametrize(
        'date_frame_type, started_date_frame, nearest_possible_date',
        [
            (0, lazy_fixture('pomodoro_in_progress'), get_time_delta({'minutes': 26})),
            (0, lazy_fixture('break_in_progress'), get_time_delta({'minutes': 16})),
            (0, lazy_fixture('pause_in_progress'), get_time_delta({'minutes': 1})),
            (1, lazy_fixture('pomodoro_in_progress'), get_time_delta({'minutes': 26})),
            (1, lazy_fixture('break_in_progress'), get_time_delta({'minutes': 16})),
            (1, lazy_fixture('pause_in_progress'), get_time_delta({'minutes': 1}))
        ]
    )
    @patch('pomodorr.frames.services.date_frame_service.timezone')
    def test_start_date_frame_finishes_current_date_frame(self, mock_timezone, date_frame_type, started_date_frame,
                                                          nearest_possible_date, task_instance):
        mock_timezone.now.return_value = nearest_possible_date

        assert started_date_frame.end is None
        assert task_instance.frames.count() == 1
        start_date_frame(task_id=task_instance.id, frame_type=date_frame_type)

        started_date_frame.refresh_from_db()
        assert started_date_frame.end is not None
        assert task_instance.frames.count() == 2

    @pytest.mark.parametrize(
        'date_frame_type',
        [0, 1, 2]
    )
    def test_start_date_frame_on_completed_task(self, date_frame_type, completed_task_instance):
        with pytest.raises(ValidationError) as exc:
            start_date_frame(task_id=completed_task_instance.id, frame_type=date_frame_type)

        assert exc.value.messages[0] == DateFrameException.messages[DateFrameException.task_already_completed]


class TestFinishDateFrame:
    @pytest.mark.parametrize(
        'tested_date_frame',
        [
            lazy_fixture('pomodoro_in_progress'),
            lazy_fixture('break_in_progress'),
            lazy_fixture('pause_in_progress')
        ]
    )
    def test_finish_date_frame_with_valid_end_datetime(self, tested_date_frame):
        finish_date_frame(date_frame_id=tested_date_frame.id)

        tested_date_frame.refresh_from_db()
        assert tested_date_frame.end is not None and tested_date_frame.duration is not None

    @pytest.mark.parametrize(
        'tested_date_frame',
        [
            lazy_fixture('pomodoro_in_progress'),
            lazy_fixture('break_in_progress'),
            lazy_fixture('pause_in_progress')
        ]
    )
    @patch('pomodorr.frames.services.date_frame_service.timezone')
    def test_finish_date_frame_with_start_greater_than_end(self, mock_datetime_now, tested_date_frame, task_instance):
        mock_datetime_now.now.return_value = get_time_delta({'minutes': 20}, ahead=False)

        with pytest.raises(ValidationError) as exc:
            finish_date_frame(date_frame_id=tested_date_frame.id)

        assert exc.value.messages[0] == DateFrameException.messages[DateFrameException.start_greater_than_end]

    @pytest.mark.parametrize(
        'tested_date_frame',
        [
            lazy_fixture('pomodoro_in_progress'),
            lazy_fixture('break_in_progress'),
            lazy_fixture('pause_in_progress')
        ]
    )
    def test_finish_date_frame_on_completed_task(self, tested_date_frame, task_instance):
        task_instance.status = 1
        task_instance.save()

        with pytest.raises(ValidationError) as exc:
            finish_date_frame(date_frame_id=tested_date_frame.id)
        assert exc.value.messages[0] == DateFrameException.messages[DateFrameException.task_already_completed]

    @patch('pomodorr.frames.services.date_frame_service.timezone')
    def test_finish_date_frame_with_breaks_saves_proper_duration(self, mock_timezone, pomodoro_in_progress_with_breaks):
        mock_timezone.now.return_value = get_time_delta({'minutes': 25})
        finish_date_frame(date_frame_id=pomodoro_in_progress_with_breaks.id)
        pomodoro_in_progress_with_breaks.refresh_from_db()

        break_frames = get_breaks_inside_date_frame(
            date_frame_object=pomodoro_in_progress_with_breaks,
            end=pomodoro_in_progress_with_breaks.end).values('start', 'end')

        breaks_duration = reduce(operator.add,
                                 (break_frame['end'] - break_frame['start'] for break_frame in break_frames),
                                 timedelta(0))

        expected_duration = math.trunc(
            (pomodoro_in_progress_with_breaks.end - pomodoro_in_progress_with_breaks.start -
             breaks_duration).seconds / 60)

        assert pomodoro_in_progress_with_breaks.end is not None
        assert pomodoro_in_progress_with_breaks.duration == timedelta(minutes=expected_duration)

    @patch('pomodorr.frames.services.date_frame_service.timezone')
    def test_finish_date_frame_with_pauses_saves_proper_duration(self, mock_timezone, pomodoro_in_progress_with_pauses,
                                                                 task_instance):
        mock_timezone.now.return_value = get_time_delta({'minutes': 25}, ahead=True)
        finish_date_frame(date_frame_id=pomodoro_in_progress_with_pauses.id)
        pomodoro_in_progress_with_pauses.refresh_from_db()

        pause_frames = get_pauses_inside_date_frame(
            date_frame_object=pomodoro_in_progress_with_pauses,
            end=pomodoro_in_progress_with_pauses.end).values('start', 'end')

        pauses_duration = reduce(operator.add,
                                 (break_frame['end'] - break_frame['start'] for break_frame in pause_frames),
                                 timedelta(0))

        expected_duration = math.trunc(
            (pomodoro_in_progress_with_pauses.end - pomodoro_in_progress_with_pauses.start -
             pauses_duration).seconds / 60)

        assert pomodoro_in_progress_with_pauses.end is not None
        assert pomodoro_in_progress_with_pauses.duration == timedelta(minutes=expected_duration)

    @patch('pomodorr.frames.services.date_frame_service.timezone')
    def test_finish_date_frame_with_breaks_and_pauses_saves_proper_duration(self, mock_timezone,
                                                                            pomodoro_in_progress_with_breaks_and_pauses):
        mock_timezone.now.return_value = get_time_delta({'minutes': 25}, ahead=True)

        finish_date_frame(date_frame_id=pomodoro_in_progress_with_breaks_and_pauses.id)

        pomodoro_in_progress_with_breaks_and_pauses.refresh_from_db()

        break_frames = get_breaks_inside_date_frame(
            date_frame_object=pomodoro_in_progress_with_breaks_and_pauses,
            end=pomodoro_in_progress_with_breaks_and_pauses.end).values('start', 'end')

        breaks_duration = reduce(operator.add,
                                 (break_frame['end'] - break_frame['start'] for break_frame in break_frames),
                                 timedelta(0))

        pause_frames = get_pauses_inside_date_frame(
            date_frame_object=pomodoro_in_progress_with_breaks_and_pauses,
            end=pomodoro_in_progress_with_breaks_and_pauses.end).values('start', 'end')

        pauses_duration = reduce(operator.add,
                                 (pause_frame['end'] - pause_frame['start'] for pause_frame in pause_frames),
                                 timedelta(0))

        breaks_and_pauses_duration = breaks_duration + pauses_duration
        expected_duration = math.trunc(
            (pomodoro_in_progress_with_breaks_and_pauses.end - pomodoro_in_progress_with_breaks_and_pauses.start -
             breaks_and_pauses_duration).seconds / 60)

        assert round(breaks_and_pauses_duration.seconds) // 60 == 10
        assert pomodoro_in_progress_with_breaks_and_pauses.end is not None
        assert pomodoro_in_progress_with_breaks_and_pauses.duration == timedelta(minutes=expected_duration)

    @pytest.mark.parametrize(
        'tested_date_frame, tested_date_frame_length, expected_error_code',
        [
            (lazy_fixture('pomodoro_in_progress'), get_time_delta({'minutes': 30}),
             DateFrameException.invalid_pomodoro_length),
            (lazy_fixture('break_in_progress'), get_time_delta({'minutes': 20}),
             DateFrameException.invalid_break_length)
        ]
    )
    @patch('pomodorr.frames.services.date_frame_service.timezone')
    def test_finish_date_frame_with_longer_than_specified_duration(self, mock_timezone, tested_date_frame,
                                                                   expected_error_code, tested_date_frame_length):
        mock_timezone.now.return_value = tested_date_frame_length

        with pytest.raises(ValidationError) as exc:
            finish_date_frame(date_frame_id=tested_date_frame.id)
        assert exc.value.messages[0] == DateFrameException.messages[expected_error_code]

    @pytest.mark.parametrize(
        'tested_date_frame, tested_date_frame_length, normalized_date_frame_duration',
        [
            (lazy_fixture('pomodoro_in_progress'), get_time_delta({'minutes': 25, 'seconds': 40}),
             timedelta(minutes=25)),
            (lazy_fixture('break_in_progress'), get_time_delta({'minutes': 15, 'seconds': 40}),
             timedelta(minutes=15))
        ]
    )
    @patch('pomodorr.frames.services.date_frame_service.timezone')
    def test_finish_date_frame_fits_within_length_error_margin(self, mock_timezone, tested_date_frame,
                                                               normalized_date_frame_duration,
                                                               tested_date_frame_length):
        mock_timezone.now.return_value = tested_date_frame_length
        finish_date_frame(date_frame_id=tested_date_frame.id)
        tested_date_frame.refresh_from_db()

        assert tested_date_frame.end is not None
        assert tested_date_frame.duration == normalized_date_frame_duration

    @pytest.mark.parametrize(
        'tested_date_frame, end_date',
        [
            (lazy_fixture('pomodoro_in_progress'), get_time_delta({'minutes': 23})),
            (lazy_fixture('break_in_progress'), get_time_delta({'minutes': 12}))
        ]
    )
    @patch('pomodorr.frames.services.date_frame_service.timezone')
    def test_force_finish_date_frame_with_proper_end_date(self, mock_timezone, tested_date_frame, end_date):
        mock_timezone.now.return_value = end_date

        finished_date_frame = force_finish_date_frame(date_frame=tested_date_frame)

        assert finished_date_frame.end == end_date

    @pytest.mark.parametrize(
        'tested_date_frame, end_date',
        [
            (lazy_fixture('pomodoro_in_progress'), get_time_delta({'minutes': 45})),
            (lazy_fixture('break_in_progress'), get_time_delta({'minutes': 19}))
        ]
    )
    @patch('pomodorr.frames.services.date_frame_service.timezone')
    def test_force_finish_date_frame_with_end_date_exceeding_estimated_date(self, mock_timezone, tested_date_frame,
                                                                            end_date):
        mock_timezone.now.return_value = end_date

        finished_date_frame = force_finish_date_frame(date_frame=tested_date_frame)

        assert finished_date_frame.end < end_date

    def test_force_finish_pause_finishes_related_pomodoro(self, pause_in_progress_with_ongoing_pomodoro):
        pause, pomodoro = pause_in_progress_with_ongoing_pomodoro

        force_finish_date_frame(date_frame=pause)

        pause.refresh_from_db()
        pomodoro.refresh_from_db()

        assert pause.end is not None
        assert pomodoro.end is not None
        assert pause.end < pomodoro.end
