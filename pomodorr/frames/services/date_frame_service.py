from datetime import datetime

from django.db import transaction
from django.utils import timezone

from pomodorr.frames.models import DateFrame
from pomodorr.frames.selectors.date_frame_selector import get_colliding_date_frame_for_task, \
    get_latest_date_frame_in_progress_for_task
from pomodorr.projects.signals.dispatchers import notify_force_finish


def finish_colliding_date_frame(task_id: int, date: datetime, excluded_id: int = None):
    colliding_date_frame = get_colliding_date_frame_for_task(task_id=task_id, date=date, excluded_id=excluded_id)

    if colliding_date_frame is not None and colliding_date_frame.end is None:
        force_finish_date_frame(date_frame=colliding_date_frame)


def start_date_frame(task_id: int, frame_type: int) -> DateFrame:
    start = timezone.now()

    with transaction.atomic():
        finish_colliding_date_frame(task_id=task_id, date=start)

        new_date_frame = DateFrame.objects.create(
            start=start,
            frame_type=frame_type,
            task_id=task_id
        )
        return new_date_frame


def finish_date_frame(date_frame_id: int) -> DateFrame:
    end = timezone.now()

    with transaction.atomic():
        try:
            date_frame = DateFrame.objects.get(id=date_frame_id)
        except DateFrame.DoesNotExist:
            raise
        else:
            finish_colliding_date_frame(task_id=date_frame.task.id, date=end, excluded_id=date_frame_id)

            date_frame.end = end
            date_frame.save()
            return date_frame


def force_finish_date_frame(task_id: int = None, date_frame: DateFrame = None) -> DateFrame:
    end = timezone.now()

    with transaction.atomic():
        if date_frame is None:
            date_frame = get_latest_date_frame_in_progress_for_task(task_id=task_id)

        if date_frame is not None:
            if end > date_frame.estimated_date_frame_end:
                date_frame.end = date_frame.estimated_date_frame_end
            else:
                date_frame.end = end
            date_frame.save()

            notify_force_finish.send(sender=force_finish_date_frame, task=date_frame.task)

            return date_frame
