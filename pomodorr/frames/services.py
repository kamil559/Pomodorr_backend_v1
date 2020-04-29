import math
import operator
from datetime import timedelta, datetime
from functools import reduce
from typing import Union

from django.core.cache import cache
from django.db import transaction
from django.db.models import Q, DurationField
from django.utils import timezone

from pomodorr.frames.exceptions import DateFrameException as DFE
from pomodorr.frames.models import DateFrame
from pomodorr.frames.selectors import DateFrameSelector, PauseSelector
from pomodorr.projects.models import Task
from pomodorr.projects.services import TaskServiceModel


class StartFrame:
    def __init__(self, task: Task, frame_type: int, start: datetime):
        self._task = task
        self._frame_type = frame_type
        self._start = start
        self.date_frame_model = DateFrame

    def execute(self):
        with transaction.atomic():
            # todo: at first finish the task's current date frame
            self.start_date_frame()

    def start_date_frame(self) -> DateFrame:
        date_frame = self.date_frame_model(task=self._task, type=self._frame_type, start=self._start)
        date_frame.full_clean()
        date_frame.save()
        return date_frame


class FinishFrame:
    def __init__(self, task: Task, end: datetime):
        self._task = task
        self._end = end
        self._current_date_frame = task.get_current_date_frame()
        self._date_frame_model = DateFrame
        self._duration_calculator = DurationCalculatorLoader(date_frame_object=self._current_date_frame, end=self._end)

    def execute(self):
        with transaction.atomic():
            self.finish_date_frame()

    def finish_date_frame(self):
        self._current_date_frame.end = self._end
        self._current_date_frame.duration = self.get_date_frame_duration()
        self._current_date_frame.save()

    def get_date_frame_duration(self) -> timedelta:
        date_frame_duration = self._duration_calculator.calculate()
        normalized_pomodoro_duration = self.normalize_pomodoro_duration(date_frame_duration=date_frame_duration)
        return normalized_pomodoro_duration

    def normalize_pomodoro_duration(self, date_frame_duration: timedelta) -> timedelta:
        error_margin = timedelta(minutes=1)
        pomodoro_length = self.get_pomodoro_length(task=self._task)
        duration_difference = date_frame_duration - pomodoro_length

        self.check_duration_fits_error_margin(duration_difference=duration_difference, error_margin=error_margin)

        if timedelta(milliseconds=1) < duration_difference < error_margin:
            truncated_minutes = math.trunc(pomodoro_length.seconds / 60)
            return timedelta(minutes=truncated_minutes)
        return date_frame_duration

    @staticmethod
    def check_duration_fits_error_margin(duration_difference: timedelta, error_margin: timedelta) -> None:
        if duration_difference > error_margin:
            raise DFE([DFE.messages[DFE.invalid_pomodoro_length]], code=DFE.invalid_pomodoro_length)

    @staticmethod
    def get_pomodoro_length(task: Task) -> timedelta:
        # user = task_event.task.project.user
        # todo: create settings module where each user will have default values for pomodoros, breaks, long breaks, etc.
        # user_global_pomodoro_length = user.pomodoro_length
        task_specific_pomodoro_length: Union[None, timedelta, DurationField] = task.pomodoro_length

        if task_specific_pomodoro_length and task_specific_pomodoro_length is not None:
            return task_specific_pomodoro_length
        # return user_global_pomodoro_length


class DurationCalculatorLoader:
    def __init__(self, date_frame_object: DateFrame, end: datetime):
        self._date_frame_model = date_frame_object.__class__

        if date_frame_object.type == self._date_frame_model.pomodoro_type:
            self._calculator_strategy = PomodoroDurationCalculator(date_frame_object=date_frame_object, end=end)
        elif date_frame_object.type == self._date_frame_model.break_type:
            self._calculator_strategy = BreakDurationCalculator(date_frame_object=date_frame_object, end=end)
        elif date_frame_object.type == self._date_frame_model.pause_type:
            self._calculator_strategy = PauseDurationCalculator(date_frame_object=date_frame_object, end=end)
        else:
            raise DFE(DFE.messages[DFE.invalid_date_frame_type])

    def calculate(self) -> timedelta:
        return self._calculator_strategy.get_duration()


class DurationCalculator:
    def __init__(self, date_frame_object: DateFrame, end):
        self._date_frame_selector = DateFrameSelector
        self._date_frame_model = date_frame_object.__class__
        self._date_frame_object = date_frame_object
        self._end = end

    def get_duration(self) -> timedelta:
        if self._date_frame_object.start > self._end:
            raise DFE(DFE.messages[DFE.start_greater_than_end])
        return self._end - self._date_frame_object.start


class PomodoroDurationCalculator(DurationCalculator):

    def get_duration(self) -> timedelta:
        whole_frame_duration = self._end - self._date_frame_object.start
        breaks_duration = self.__get_breaks_duration()
        pauses_duration = self.__get_pauses_duration()
        return whole_frame_duration - breaks_duration - pauses_duration

    def __get_breaks_duration(self) -> timedelta:
        break_frames = self._date_frame_selector.get_breaks_inside_date_frame(date_frame_object=self._date_frame_object,
                                                                              end=self._end).values_list('start', 'end')
        breaks_duration = reduce(operator.add, (break_frame.end - break_frame.start for break_frame in break_frames),
                                 timedelta(0))
        return breaks_duration

    def __get_pauses_duration(self) -> timedelta:
        pause_frames = self._date_frame_selector.get_pauses_inside_date_frame(date_frame_object=self._date_frame_object,
                                                                              end=self._end).values_list('start', 'end')
        pauses_duration = reduce(operator.add, (pause_frame.end - pause_frame.start for pause_frame in pause_frames),
                                 timedelta(0))
        return pauses_duration


class BreakDurationCalculator(DurationCalculator):
    pass


class PauseDurationCalculator(DurationCalculator):
    pass


class DateFrameServiceModel:
    model = DateFrame
    task_service_model = TaskServiceModel()
    date_frame_selector = DateFrameSelector
    pause_selector = PauseSelector

    def start_date_frame(self, task: Task, frame_type: int):
        self.task_service_model.check_task_already_completed(task=task)
        frame_start = timezone.now()

        self.check_current_date_frame_already_exists(task=task, remove_outdated=True)
        self.check_datetime_available(task=task, start_date=frame_start)

        new_pomodoro = self.perform_frame_create(task=task, start=frame_start)
        return new_pomodoro

    def finish_date_frame(self, task_event, remove_unfinished_gaps=False):
        self.task_service_model.check_task_already_completed(task=task_event.task)
        finish_datetime = timezone.now()
        duration = self.get_task_event_duration(task_event=task_event, finish_datetime=finish_datetime)

        self.check_datetime_available(task=task_event.task, start_date=task_event.start, end_date=finish_datetime,
                                      excluded_task_event=task_event)

        task_event.end, task_event.duration = finish_datetime, duration
        task_event.save()

        if remove_unfinished_gaps:
            self.remove_gaps(task_event=task_event)

        return task_event

    @classmethod
    def check_datetime_available(cls, task, start_date, end_date=None, excluded_task_event=None):
        today = timezone.now().date()

        active_task_events_constraint = Q(start__isnull=False) & Q(end__isnull=True)
        completed_task_events_constraint = Q(start__isnull=False) & Q(end__isnull=False)
        today_date_constraint = Q(start__date=today) & Q(end__date=today)

        start_constraint, end_constraint = (Q(start__gte=start_date), Q(end__gte=start_date))

        overlapping_task_events = cls.date_frame_selector.get_all_date_frames_for_task(
            task=task).filter(
            (active_task_events_constraint | completed_task_events_constraint) &
            today_date_constraint & (
                start_constraint | end_constraint
            )
        )

        if end_date is not None:
            start_constraint, end_constraint = (Q(start__gte=end_date), Q(end__gte=end_date))
            overlapping_task_events = overlapping_task_events.filter(
                start_constraint | end_constraint
            )

        if excluded_task_event is not None:
            overlapping_task_events = overlapping_task_events.exclude(id=excluded_task_event.id)

        if overlapping_task_events.exists():
            raise DFE([DFE.messages[DFE.overlapping_pomodoro]],
                      code=DFE.overlapping_pomodoro)

    def perform_frame_create(self, task, start):
        pomodoro = self.model(task=task, start=start)
        pomodoro.full_clean()
        pomodoro.save()

        return pomodoro

    def get_task_event_duration(self, task_event, finish_datetime):
        gaps_duration = reduce(operator.add, (gap.end - gap.start for gap in task_event.gaps.all()), timedelta(0))
        duration_without_gaps = finish_datetime - task_event.start - gaps_duration

        normalized_pomodoro_duration = self.normalize_pomodoro_duration(task_event=task_event,
                                                                        task_event_duration=duration_without_gaps,
                                                                        error_margin={'minutes': 1})

        return normalized_pomodoro_duration

    def normalize_pomodoro_duration(self, task_event_duration, task_event, error_margin):
        error_margin = timedelta(**error_margin)
        pomodoro_length = self.get_pomodoro_length(task=task_event.task)
        duration_difference = task_event_duration - pomodoro_length

        if duration_difference > error_margin:
            raise DFE([DFE.messages[DFE.invalid_pomodoro_length]],
                      code=DFE.invalid_pomodoro_length)

        if timedelta(milliseconds=1) < duration_difference < error_margin:
            truncated_minutes = math.trunc(pomodoro_length.seconds / 60)
            return timedelta(minutes=truncated_minutes)

        return task_event_duration

    @staticmethod
    def get_pomodoro_length(task):
        # user = task_event.task.project.user
        # todo: create settings module where each user will have default values for pomodoros, breaks, long breaks, etc.
        # user_global_pomodoro_length = user.pomodoro_length
        task_specific_pomodoro_length = task.pomodoro_length

        if task_specific_pomodoro_length and task_specific_pomodoro_length is not None:
            return task_specific_pomodoro_length
        # return user_global_pomodoro_length

    def check_current_date_frame_already_exists(self, task, remove_outdated=False):
        current_task_event = self.date_frame_selector.get_current_date_frame_for_task(task=task)

        if current_task_event is not None:
            self.check_current_task_event_is_connected(task_event=current_task_event)

        if remove_outdated:
            self.remove_task_event(task_event=current_task_event)

    @staticmethod
    def check_current_task_event_is_connected(task_event):
        connection_id = cache.get(task_event.id)

        if connection_id and connection_id is not None:
            raise DFE([DFE.messages[DFE.current_pomodoro_exists]], code=DFE.current_pomodoro_exists)

    def remove_gaps(self, task_event):
        unfinished_gaps = self.pause_selector.get_unfinished_pauses(task_event=task_event)
        unfinished_gaps.delete()

    @staticmethod
    def remove_task_event(task_event):
        if task_event is not None:
            task_event.delete()
