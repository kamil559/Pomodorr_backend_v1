from django.db import transaction
from django.utils import timezone

from pomodorr.frames.models import DateFrame
from pomodorr.frames.selectors.date_frame_selector import get_colliding_date_frame_for_task, \
    get_latest_date_frame_in_progress_for_task


def start_date_frame(task_id: int, frame_type: int) -> DateFrame:
    start = timezone.now()

    with transaction.atomic():
        colliding_date_frame = get_colliding_date_frame_for_task(task_id=task_id, start=start)
        if colliding_date_frame is not None:
            finish_date_frame(date_frame_id=colliding_date_frame.id)

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
            date_frame.end = end
            date_frame.save()
            return date_frame


def force_finish_date_frame(task_id: int) -> DateFrame:
    end = timezone.now()

    with transaction.atomic():
        current_date_frame = get_latest_date_frame_in_progress_for_task(task_id=task_id)

        if current_date_frame is None:
            return

        if end > current_date_frame.estimated_date_frame_end:
            current_date_frame.end = current_date_frame.estimated_date_frame_end
        else:
            current_date_frame.end = end
        current_date_frame.save()

        return current_date_frame
