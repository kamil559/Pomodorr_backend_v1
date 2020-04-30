import random
from datetime import timedelta

import factory
from django.utils import timezone
from factory.fuzzy import FuzzyAttribute

from pomodorr.frames.models import DateFrame


class DateFrameFactory(factory.DjangoModelFactory):
    start = factory.LazyFunction(timezone.now)
    end = factory.LazyAttribute(lambda n: n.start + timedelta(minutes=25))
    frame_type = FuzzyAttribute(lambda: random.randint(0, 2))

    class Meta:
        model = DateFrame


class BreakDateFrameFactory(factory.DjangoModelFactory):
    start = factory.LazyFunction(timezone.now)
    end = factory.LazyAttribute(lambda n: n.start + timedelta(minutes=2))
    frame_type = FuzzyAttribute(lambda: random.randint(0, 2))

    class Meta:
        model = DateFrame
