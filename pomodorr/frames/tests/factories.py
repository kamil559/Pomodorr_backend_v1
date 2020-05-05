import random
from datetime import timedelta

import factory
from django.utils import timezone
from factory.fuzzy import FuzzyAttribute

from pomodorr.frames.models import DateFrame


class DateFrameFactory(factory.DjangoModelFactory):
    start = factory.LazyFunction(timezone.now)
    end = factory.LazyAttribute(lambda n: n.start + timedelta(minutes=25))
    frame_type = 0

    class Meta:
        model = DateFrame


def get_duration(instance):
    if instance.frame_type == 0:
        return instance.task.normalized_pomodoro_length
    elif instance.frame_type == 1:
        return instance.task.normalized_break_length
    return timedelta(minutes=5)


class InnerDateFrameFactory(factory.DjangoModelFactory):
    start = factory.Sequence(lambda n: timezone.now() + timedelta(minutes=(25 * n) + 2))
    frame_type = FuzzyAttribute(lambda: random.randint(0, 2))
    end = factory.LazyAttribute(lambda n: n.start + get_duration(instance=n))

    class Meta:
        model = DateFrame
