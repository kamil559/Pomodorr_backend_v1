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
        'date_frame_type',
        [0, 1, 2]
    )
    def test_start_date_frame_finishes_current_date_frame(self, date_frame_type, task_instance, date_frame_in_progress):
        assert date_frame_in_progress.end is None
        assert task_instance.frames.count() == 1
        start_frame_command = StartFrame(task=task_instance, frame_type=date_frame_type, start=timezone.now())
        start_frame_command.execute()

        date_frame_in_progress.refresh_from_db()
        assert date_frame_in_progress.end is not None
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
        'date_frame_type',
        [0, 1, 2]
    )
    def test_start_date_frame_with_overlapping_start_date(self, date_frame_type, task_instance,
                                                          date_frame_create_batch):
        start_frame_command = StartFrame(task=task_instance, frame_type=date_frame_type, start=timezone.now())
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
        finish_frame_command = FinishFrame(task=task_instance, end=timezone.now())

        with pytest.raises(ValidationError) as exc:
            finish_frame_command.execute()
        assert exc.value.messages[0] == DateFrameException.messages[DateFrameException.task_already_completed]

    @pytest.mark.parametrize(
        'tested_date_frame',
        [
            lazy_fixture('pomodoro_in_progress'),
            lazy_fixture('break_in_progress'),
            lazy_fixture('pause_in_progress')
        ]
    )
    def test_finish_date_frame_with_overlapping_start_date(self, tested_date_frame, date_frame_create_batch,
                                                           task_instance):
        finish_frame_command = FinishFrame(task=task_instance, end=timezone.now())
        with pytest.raises(ValidationError) as exc:
            finish_frame_command.execute()
        assert exc.value.messages[0] == DateFrameException.messages[DateFrameException.overlapping_date_frame]

    @patch('pomodorr.frames.tests.test_services.timezone')
    def test_finish_date_frame_with_breaks_saves_proper_duration(self, mock_timezone, pomodoro_in_progress_with_breaks,
                                                                 task_instance,
                                                                 date_frame_selector):
        mock_timezone.now.return_value = get_time_delta({'minutes': 25})
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

    def test_finish_date_frame_with_pauses_saves_proper_duration(self):
        pass

    def test_finish_date_frame_with_breaks_and_pauses_saves_proper_duration(self):
        pass

    def test_finish_date_frame_with_shorter_than_specified_duration(self):
        pass

    def test_finish_date_frame_with_longer_than_specified_duration(self):
        pass
