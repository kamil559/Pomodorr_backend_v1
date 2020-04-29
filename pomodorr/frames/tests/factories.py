from datetime import timedelta

import factory
from django.utils import timezone

from pomodorr.frames.models import DateFrame


class DateFrameFactory(factory.DjangoModelFactory):
    start = factory.LazyFunction(timezone.now)
    end = factory.LazyAttribute(lambda n: n.start + timedelta(minutes=25))

    class Meta:
        model = DateFrame
