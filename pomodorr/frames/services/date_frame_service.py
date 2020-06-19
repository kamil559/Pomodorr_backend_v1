from datetime import datetime
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from pomodorr.frames.models import DateFrame
from pomodorr.frames.selectors.date_frame_selector import (
    get_colliding_date_frame_for_task, get_latest_date_frame_in_progress_for_task)
from pomodorr.projects.signals.dispatchers import notify_force_finish


def force_finish_date_frame(task_id: UUID = None, date_frame: DateFrame = None, notify: bool = True) -> DateFrame:
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

            if date_frame.frame_type == DateFrame.pause_type:
                finish_related_pomodoro(date_frame=date_frame)

            if notify:
                notify_force_finish.send(sender=force_finish_date_frame, task=date_frame.task)

            return date_frame


def finish_colliding_date_frame(task_id: UUID, date: datetime, excluded_id: UUID = None):
    colliding_date_frame = get_colliding_date_frame_for_task(task_id=task_id, date=date, excluded_id=excluded_id)

    if colliding_date_frame is not None and colliding_date_frame.end is None:
        finish_date_frame(date_frame_id=colliding_date_frame.id)


def finish_date_frame(date_frame_id: UUID) -> DateFrame:
    end = timezone.now()

    with transaction.atomic():
        try:
            date_frame = DateFrame.objects.get(id=date_frame_id)
        except DateFrame.DoesNotExist:
            raise
        else:
            if date_frame.frame_type in [DateFrame.pomodoro_type, DateFrame.break_type]:
                finish_colliding_date_frame(task_id=date_frame.task.id, date=end, excluded_id=date_frame_id)

            date_frame.end = end
            date_frame.save()
            return date_frame


def finish_related_pomodoro(date_frame: DateFrame) -> None:
    try:
        previous_date_frame = date_frame.get_previous_by_created(
            task=date_frame.task,
            end__isnull=True,
            frame_type=DateFrame.pomodoro_type,
            created__date=date_frame.created.date()
        )
    except DateFrame.DoesNotExist:
        pass
    else:
        finish_date_frame(date_frame_id=previous_date_frame.id)


def start_date_frame(task_id: UUID, frame_type: int) -> DateFrame:
    start = timezone.now()

    with transaction.atomic():
        if frame_type in [DateFrame.pomodoro_type, DateFrame.break_type]:
            finish_colliding_date_frame(task_id=task_id, date=start)

        new_date_frame = DateFrame.objects.create(
            start=start,
            frame_type=frame_type,
            task_id=task_id
        )
        return new_date_frame
