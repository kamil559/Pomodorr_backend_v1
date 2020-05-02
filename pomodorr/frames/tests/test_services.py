import operator
from datetime import timedelta
from functools import reduce
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from pytest_lazyfixture import lazy_fixture

from pomodorr.frames.exceptions import DateFrameException
from pomodorr.frames.services import StartFrame, FinishFrame
from pomodorr.tools.utils import get_time_delta

pytestmark = pytest.mark.django_db()


class TestStartDateFrame:

    @pytest.mark.parametrize(
        'date_frame_type',
        [0, 1, 2]
    )
    def test_start_date_frame_with_valid_start_datetime(self, date_frame_type, task_instance):
        start_frame_command = StartFrame(task=task_instance, frame_type=date_frame_type, start=timezone.now())
        assert task_instance.frames.count() == 0
        start_frame_command.execute()
        assert task_instance.frames.count() == 1

    @pytest.mark.parametrize(
        'date_frame_type, started_date_frame, nearest_possible_date',
        [
            (0, lazy_fixture('pomodoro_in_progress'), get_time_delta({'minutes': 26})),
            (0, lazy_fixture('break_in_progress'), get_time_delta({'minutes': 16})),
            (0, lazy_fixture('pause_in_progress'), get_time_delta({'minutes': 1})),
            (1, lazy_fixture('pomodoro_in_progress'), get_time_delta({'minutes': 26})),
            (1, lazy_fixture('break_in_progress'), get_time_delta({'minutes': 16})),
            (1, lazy_fixture('pause_in_progress'), get_time_delta({'minutes': 1})),
            (2, lazy_fixture('pomodoro_in_progress'), get_time_delta({'minutes': 26})),
            (2, lazy_fixture('break_in_progress'), get_time_delta({'minutes': 16})),
            (2, lazy_fixture('pause_in_progress'), get_time_delta({'minutes': 1}))
        ]
    )
    def test_start_date_frame_finishes_current_date_frame(self, date_frame_type, started_date_frame,
                                                          nearest_possible_date, task_instance):
        assert started_date_frame.end is None
        assert task_instance.frames.count() == 1
        start_frame_command = StartFrame(task=task_instance, frame_type=date_frame_type, start=nearest_possible_date)
        start_frame_command.execute()

        started_date_frame.refresh_from_db()
        assert started_date_frame.end is not None
        assert task_instance.frames.count() == 2

    @pytest.mark.parametrize(
        'date_frame_type',
        [0, 1, 2]
    )
    def test_start_date_frame_on_completed_task(self, date_frame_type, completed_task_instance):
        start_frame_command = StartFrame(task=completed_task_instance, frame_type=date_frame_type, start=timezone.now())

        with pytest.raises(ValidationError) as exc:
            start_frame_command.execute()

        assert exc.value.messages[0] == DateFrameException.messages[DateFrameException.task_already_completed]

    @pytest.mark.parametrize(
        'date_frame_type, started_date_frame, invalid_end_date',
        [
            (0, lazy_fixture('pomodoro_in_progress'), get_time_delta({'minutes': 24})),
            (0, lazy_fixture('break_in_progress'), get_time_delta({'minutes': 14})),
            (1, lazy_fixture('pomodoro_in_progress'), get_time_delta({'minutes': 24})),
            (1, lazy_fixture('break_in_progress'), get_time_delta({'minutes': 14})),
            (2, lazy_fixture('pomodoro_in_progress'), get_time_delta({'minutes': 24})),
            (2, lazy_fixture('break_in_progress'), get_time_delta({'minutes': 14})),
        ]
    )
    def test_start_date_frame_with_overlapping_start_date(self, date_frame_type, started_date_frame, task_instance,
                                                          invalid_end_date):
        start_frame_command = StartFrame(task=task_instance, frame_type=date_frame_type, start=invalid_end_date)
        with pytest.raises(ValidationError) as exc:
            start_frame_command.execute()
        assert exc.value.messages[0] == DateFrameException.messages[DateFrameException.overlapping_date_frame]


class TestFinishDateFrame:
    @pytest.mark.parametrize(
        'tested_date_frame',
        [
            lazy_fixture('pomodoro_in_progress'),
            lazy_fixture('break_in_progress'),
            lazy_fixture('pause_in_progress')
        ]
    )
    def test_finish_date_frame_with_valid_end_datetime(self, tested_date_frame, task_instance):
        finish_frame_command = FinishFrame(task=task_instance, end=timezone.now())
        finish_frame_command.execute()

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
    def test_finish_date_frame_with_start_greater_than_end(self, tested_date_frame, task_instance):
        finish_frame_command = FinishFrame(task=task_instance, end=get_time_delta({'minutes': 20}, ahead=False))

        with pytest.raises(ValidationError) as exc:
            finish_frame_command.execute()

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
        finish_frame_command = FinishFrame(task=task_instance, end=timezone.now())

        with pytest.raises(ValidationError) as exc:
            finish_frame_command.execute()
        assert exc.value.messages[0] == DateFrameException.messages[DateFrameException.task_already_completed]

    @pytest.mark.parametrize(
        'started_date_frame, invalid_end_date',
        [
            (lazy_fixture('pomodoro_in_progress'), get_time_delta({'minutes': 24})),
            (lazy_fixture('break_in_progress'), get_time_delta({'minutes': 14})),
            (lazy_fixture('pomodoro_in_progress'), get_time_delta({'minutes': 24})),
            (lazy_fixture('break_in_progress'), get_time_delta({'minutes': 14})),
            (lazy_fixture('pomodoro_in_progress'), get_time_delta({'minutes': 24})),
            (lazy_fixture('break_in_progress'), get_time_delta({'minutes': 14})),
        ]
    )
    def test_finish_date_frame_with_overlapping_start_date(self, started_date_frame, invalid_end_date, task_instance,
                                                           date_frame_instance):
        finish_frame_command = FinishFrame(task=task_instance, end=invalid_end_date)
        with pytest.raises(ValidationError) as exc:
            finish_frame_command.execute()
        assert exc.value.messages[0] == DateFrameException.messages[DateFrameException.overlapping_date_frame]

    @patch('pomodorr.frames.tests.test_services.timezone')
    def test_finish_date_frame_with_breaks_saves_proper_duration(self, mock_timezone, pomodoro_in_progress_with_breaks,
                                                                 task_instance, date_frame_selector):
        mock_timezone.now.return_value = get_time_delta({'minutes': 25}, ahead=True)
        date_frame_end = timezone.now()
        finish_frame_command = FinishFrame(task=task_instance, end=date_frame_end)
        finish_frame_command.execute()
        pomodoro_in_progress_with_breaks.refresh_from_db()

        break_frames = date_frame_selector.get_breaks_inside_date_frame(
            date_frame_object=pomodoro_in_progress_with_breaks, end=date_frame_end).values('start', 'end')
        breaks_duration = reduce(operator.add,
                                 (break_frame['end'] - break_frame['start'] for break_frame in break_frames),
                                 timedelta(0))

        expected_duration = date_frame_end - pomodoro_in_progress_with_breaks.start - breaks_duration
        assert pomodoro_in_progress_with_breaks.end is not None
        assert pomodoro_in_progress_with_breaks.duration == expected_duration

    @patch('pomodorr.frames.tests.test_services.timezone')
    def test_finish_date_frame_with_pauses_saves_proper_duration(self, mock_timezone, pomodoro_in_progress_with_pauses,
                                                                 task_instance, date_frame_selector):
        mock_timezone.now.return_value = get_time_delta({'minutes': 25}, ahead=True)
        date_frame_end = timezone.now()
        finish_frame_command = FinishFrame(task=task_instance, end=date_frame_end)
        finish_frame_command.execute()
        pomodoro_in_progress_with_pauses.refresh_from_db()

        pause_frames = date_frame_selector.get_pauses_inside_date_frame(
            date_frame_object=pomodoro_in_progress_with_pauses, end=date_frame_end).values('start', 'end')
        pauses_duration = reduce(operator.add,
                                 (break_frame['end'] - break_frame['start'] for break_frame in pause_frames),
                                 timedelta(0))

        expected_duration = date_frame_end - pomodoro_in_progress_with_pauses.start - pauses_duration
        assert pomodoro_in_progress_with_pauses.end is not None
        assert pomodoro_in_progress_with_pauses.duration == expected_duration

    @patch('pomodorr.frames.tests.test_services.timezone')
    def test_finish_date_frame_with_breaks_and_pauses_saves_proper_duration(self, mock_timezone,
                                                                            pomodoro_in_progress_with_breaks_and_pauses,
                                                                            task_instance, date_frame_selector):
        mock_timezone.now.return_value = get_time_delta({'minutes': 25}, ahead=True)
        date_frame_end = timezone.now()
        finish_frame_command = FinishFrame(task=task_instance, end=date_frame_end)
        finish_frame_command.execute()
        pomodoro_in_progress_with_breaks_and_pauses.refresh_from_db()

        break_frames = date_frame_selector.get_breaks_inside_date_frame(
            date_frame_object=pomodoro_in_progress_with_breaks_and_pauses, end=date_frame_end).values('start', 'end')
        breaks_duration = reduce(operator.add,
                                 (break_frame['end'] - break_frame['start'] for break_frame in break_frames),
                                 timedelta(0))
        pause_frames = date_frame_selector.get_pauses_inside_date_frame(
            date_frame_object=pomodoro_in_progress_with_breaks_and_pauses, end=date_frame_end).values('start', 'end')
        pauses_duration = reduce(operator.add,
                                 (pause_frame['end'] - pause_frame['start'] for pause_frame in pause_frames),
                                 timedelta(0))

        breaks_and_pauses_duration = breaks_duration + pauses_duration
        expected_duration = date_frame_end - pomodoro_in_progress_with_breaks_and_pauses.start - \
                            breaks_and_pauses_duration

        assert round(expected_duration.total_seconds()) // 60 == 15
        assert round(breaks_and_pauses_duration.seconds) // 60 == 10
        assert pomodoro_in_progress_with_breaks_and_pauses.end is not None
        assert pomodoro_in_progress_with_breaks_and_pauses.duration == expected_duration

    @pytest.mark.parametrize(
        'tested_date_frame, tested_date_frame_length, expected_error_code',
        [
            (lazy_fixture('pomodoro_in_progress'), get_time_delta({'minutes': 30}),
             DateFrameException.invalid_pomodoro_length),
            (lazy_fixture('break_in_progress'), get_time_delta({'minutes': 20}),
             DateFrameException.invalid_break_length)
        ]
    )
    @patch('pomodorr.frames.tests.test_services.timezone')
    def test_finish_date_frame_with_longer_than_specified_duration(self, mock_timezone, tested_date_frame,
                                                                   expected_error_code, tested_date_frame_length,
                                                                   task_instance):
        mock_timezone.now.return_value = tested_date_frame_length
        finish_frame_command = FinishFrame(task=task_instance, end=timezone.now())

        with pytest.raises(ValidationError) as exc:
            finish_frame_command.execute()
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
    @patch('pomodorr.frames.tests.test_services.timezone')
    def test_finish_date_frame_fits_within_length_error_margin(self, mock_timezone, tested_date_frame,
                                                               normalized_date_frame_duration, tested_date_frame_length,
                                                               task_instance):
        mock_timezone.now.return_value = tested_date_frame_length
        finish_frame_command = FinishFrame(task=task_instance, end=timezone.now())
        finish_frame_command.execute()
        tested_date_frame.refresh_from_db()

        assert tested_date_frame.end is not None
        assert tested_date_frame.duration == normalized_date_frame_duration
