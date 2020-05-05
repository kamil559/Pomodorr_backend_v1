from datetime import datetime
from typing import Optional

from django.db import transaction

from pomodorr.frames.models import DateFrame
from pomodorr.frames.selectors import DateFrameSelector
from pomodorr.projects.models import Task
from pomodorr.projects.selectors import TaskSelector
from pomodorr.projects.services import TaskServiceModel


class DateFrameCommand:
    def __init__(self, task: Task, start: datetime = None, frame_type: int = None, end: Optional[datetime] = None,
                 *args, **kwargs):
        self._task_service_model = TaskServiceModel()
        self._task_selector_class = TaskSelector
        self._date_frame_selector_class = DateFrameSelector(model_class=DateFrame)
        self._task = task
        self._frame_type = frame_type
        self._start = start
        self._end = end
        self._date_frame_model = DateFrame


class StartFrame(DateFrameCommand):
    def __init__(self, *args, **kwargs):
        super(StartFrame, self).__init__(*args, **kwargs)
        self._colliding_data_frame = self._date_frame_selector_class.get_colliding_date_frame_for_task(
            task=self._task, start=self._start)

    def execute(self) -> None:
        with transaction.atomic():
            if self._colliding_data_frame is not None:
                self.finish_colliding_date_frame()
            self.start_date_frame()

    def start_date_frame(self) -> None:
        date_frame = self._date_frame_model(task=self._task, frame_type=self._frame_type, start=self._start)
        date_frame.full_clean()
        date_frame.save()

    def finish_colliding_date_frame(self) -> None:
        self._task_service_model.finish_colliding_date_frame(
            colliding_date_frame=self._colliding_data_frame, now=self._start)


class FinishFrame(DateFrameCommand):
    def __init__(self, *args, **kwargs):
        super(FinishFrame, self).__init__(*args, **kwargs)
        self._current_date_frame = self._date_frame_selector_class.get_latest_date_frame_in_progress_for_task(
            task=self._task)
        self._colliding_data_frame = self._date_frame_selector_class.get_colliding_date_frame_for_task(
            task=self._task, end=self._end, excluded_id=self._current_date_frame.id)

    def execute(self) -> None:
        with transaction.atomic():
            if self._colliding_data_frame is not None:
                self.finish_colliding_date_frame()
            self.finish_date_frame()

    def finish_date_frame(self) -> None:
        self._current_date_frame.end = self._end
        self._current_date_frame.save()

    def finish_colliding_date_frame(self) -> None:
        self._task_service_model.finish_colliding_date_frame(
            colliding_date_frame=self._colliding_data_frame, now=self._end)
