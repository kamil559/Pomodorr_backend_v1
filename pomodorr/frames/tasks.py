from config import celery_app
from pomodorr.frames.selectors.date_frame_selector import get_obsolete_date_frames


@celery_app.task(name='pomodorr.frames.clean_obsolete_date_frames')
def clean_obsolete_date_frames() -> None:
    get_obsolete_date_frames().delete()
