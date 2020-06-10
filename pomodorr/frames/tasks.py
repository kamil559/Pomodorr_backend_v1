from config import celery_app
from pomodorr.frames.services.date_frame_service import clean_date_frames


@celery_app.task(name='pomodorr.frames.clean_obsolete_date_frames')
def clean_obsolete_date_frames() -> None:
    clean_date_frames()
