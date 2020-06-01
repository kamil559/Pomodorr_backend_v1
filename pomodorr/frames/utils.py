import operator
from datetime import timedelta
from functools import reduce

from pomodorr.frames.exceptions import DateFrameException as DFE
from pomodorr.frames.selectors.date_frame_selector import get_breaks_inside_date_frame, get_pauses_inside_date_frame


class DurationCalculatorLoader:
    def __init__(self, date_frame_object, end):
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
    def __init__(self, date_frame_object, end):
        self._date_frame_object = date_frame_object
        self._date_frame_model = self._date_frame_object.__class__
        self._end = end

    def get_duration(self) -> timedelta:
        return self._end - self._date_frame_object.start


class PomodoroDurationCalculator(DurationCalculator):
    def get_duration(self) -> timedelta:
        whole_frame_duration = self._end - self._date_frame_object.start
        breaks_duration = self.get_breaks_duration()
        pauses_duration = self.get_pauses_duration()
        return whole_frame_duration - breaks_duration - pauses_duration

    def get_breaks_duration(self) -> timedelta:
        break_frames = get_breaks_inside_date_frame(
            date_frame_object=self._date_frame_object, end=self._end).values('start', 'end')
        breaks_duration = reduce(operator.add,
                                 (break_frame['end'] - break_frame['start'] for break_frame in break_frames),
                                 timedelta(0))
        return breaks_duration

    def get_pauses_duration(self) -> timedelta:
        pause_frames = get_pauses_inside_date_frame(
            date_frame_object=self._date_frame_object, end=self._end).values('start', 'end')
        pauses_duration = reduce(operator.add,
                                 (pause_frame['end'] - pause_frame['start'] for pause_frame in pause_frames),
                                 timedelta(0))
        return pauses_duration


class BreakDurationCalculator(DurationCalculator):
    pass


class PauseDurationCalculator(DurationCalculator):
    pass
