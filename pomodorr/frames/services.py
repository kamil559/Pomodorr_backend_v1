import operator
from datetime import timedelta, datetime
from functools import reduce
from typing import Optional

from django.db import transaction

from pomodorr.frames.exceptions import DateFrameException as DFE
from pomodorr.frames.models import DateFrame
from pomodorr.frames.selectors import DateFrameSelector
from pomodorr.projects.models import Task
from pomodorr.projects.selectors import TaskSelector
from pomodorr.projects.services import TaskServiceModel


class DateFrameCommand:
    def __init__(self, task: Task, start: datetime = None, frame_type: int = None, end: Optional[datetime] = None):
        self._task_service_model = TaskServiceModel()
        self._task_selector_class = TaskSelector
        self._task = task
        self._frame_type = frame_type
        self._start = start
        self._end = end
        self._date_frame_model = DateFrame


class StartFrame(DateFrameCommand):
    def execute(self) -> None:
        with transaction.atomic():
            self.finish_current_date_frame()
            self.start_date_frame()

    def start_date_frame(self) -> None:
        date_frame = self._date_frame_model(task=self._task, frame_type=self._frame_type, start=self._start)
        date_frame.full_clean()
        date_frame.save()

    def finish_current_date_frame(self) -> None:
        current_date_frame = self._task_selector_class.get_current_date_frame_for_task(task=self._task)
        if current_date_frame is not None:
            current_date_frame.end = self._start
            current_date_frame.save()


class FinishFrame(DateFrameCommand):
    def __init__(self, *args, **kwargs):
        super(FinishFrame, self).__init__(*args, **kwargs)
        self._current_date_frame = self._task_selector_class.get_current_date_frame_for_task(task=self._task)
        self._duration_calculator = DurationCalculatorLoader(date_frame_object=self._current_date_frame, end=self._end)

    def execute(self) -> None:
        with transaction.atomic():
            self.finish_date_frame()

    def finish_date_frame(self) -> None:
        self._current_date_frame.end = self._end
        self._current_date_frame.duration = self.get_date_frame_duration()
        self._current_date_frame.save()

    def get_date_frame_duration(self) -> timedelta:
        date_frame_duration = self._duration_calculator.calculate()
        return date_frame_duration


class DurationCalculatorLoader:
    def __init__(self, date_frame_object: DateFrame, end: datetime):
        self._date_frame_model = date_frame_object.__class__

        if date_frame_object.frame_type == self._date_frame_model.pomodoro_type:
            self._calculator_strategy = PomodoroDurationCalculator(date_frame_object=date_frame_object, end=end)
        elif date_frame_object.frame_type == self._date_frame_model.break_type:
            self._calculator_strategy = BreakDurationCalculator(date_frame_object=date_frame_object, end=end)
        elif date_frame_object.frame_type == self._date_frame_model.pause_type:
            self._calculator_strategy = PauseDurationCalculator(date_frame_object=date_frame_object, end=end)
        else:
            raise DFE(DFE.messages[DFE.invalid_date_frame_type])

    def calculate(self) -> timedelta:
        return self._calculator_strategy.get_duration()


class DurationCalculator:
    def __init__(self, date_frame_object: DateFrame, end):
        self._date_frame_object = date_frame_object
        self._end = end

    def get_duration(self) -> timedelta:
        return self._end - self._date_frame_object.start


class PomodoroDurationCalculator(DurationCalculator):
    def __init__(self, *args, **kwargs):
        super(PomodoroDurationCalculator, self).__init__(*args, **kwargs)
        self._date_frame_selector = DateFrameSelector(model_class=DateFrame)
        self._date_frame_model = self._date_frame_object.__class__

    def get_duration(self) -> timedelta:
        whole_frame_duration = self._end - self._date_frame_object.start
        breaks_duration = self.__get_breaks_duration()
        pauses_duration = self.__get_pauses_duration()
        return whole_frame_duration - breaks_duration - pauses_duration

    def __get_breaks_duration(self) -> timedelta:
        break_frames = self._date_frame_selector.get_breaks_inside_date_frame(
            date_frame_object=self._date_frame_object, end=self._end).values('start', 'end')
        breaks_duration = reduce(operator.add,
                                 (break_frame['end'] - break_frame['start'] for break_frame in break_frames),
                                 timedelta(0))
        return breaks_duration

    def __get_pauses_duration(self) -> timedelta:
        pause_frames = self._date_frame_selector.get_pauses_inside_date_frame(
            date_frame_object=self._date_frame_object, end=self._end).values('start', 'end')
        pauses_duration = reduce(operator.add,
                                 (pause_frame['end'] - pause_frame['start'] for pause_frame in pause_frames),
                                 timedelta(0))
        return pauses_duration


class BreakDurationCalculator(DurationCalculator):
    pass


class PauseDurationCalculator(DurationCalculator):
    pass
