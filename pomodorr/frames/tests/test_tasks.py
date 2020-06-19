import pytest

from pomodorr.frames.models import DateFrame
from pomodorr.frames.tasks import clean_obsolete_date_frames


@pytest.mark.django_db
def test_clean_obsolete_date_frames(obsolete_date_frames):
    assert DateFrame.objects.exists()

    clean_obsolete_date_frames.apply()

    assert DateFrame.objects.exists() is False
