from datetime import timedelta

import factory
from django.utils import timezone

from pomodorr.frames.models import TaskEvent, Gap
from pomodorr.tools.utils import get_time_delta


class TaskEventFactory(factory.DjangoModelFactory):
    start = factory.LazyFunction(timezone.now)
    end = factory.LazyAttribute(lambda n: n.start + timedelta(minutes=25))

    class Meta:
        model = TaskEvent


class GapFactory(factory.DjangoModelFactory):
    start = factory.Sequence(lambda n: get_time_delta({'minutes': n * 3}))
    end = factory.LazyAttribute(lambda n: n.start + timedelta(minutes=1))

    class Meta:
        model = Gap
