import random
from datetime import timedelta

import factory
from django.utils import timezone

from pomodorr.projects.models import Project, Priority, Task, SubTask, TaskEvent


class PriorityFactory(factory.DjangoModelFactory):
    priority_level = factory.Sequence(lambda n: n)
    name = factory.LazyAttribute(lambda priority_level: f'Priority level: {priority_level}')
    color = factory.Faker('color')

    class Meta:
        model = Priority


class ProjectFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: f'Project number: {n}')
    user_defined_ordering = factory.LazyAttribute(lambda x: random.randint(1, 50))

    class Meta:
        model = Project


class TaskFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: f'Task: {n}')
    user_defined_ordering = factory.LazyAttribute(lambda n: random.randint(1, 50))
    pomodoro_number = factory.LazyAttribute(lambda n: random.randint(1, 50))
    repeat_duration = factory.LazyAttribute(lambda n: timedelta(hours=random.randint(1, 24)))
    note = factory.Faker('text')

    class Meta:
        model = Task


class SubTaskFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: f'SubTask {n}')
    is_completed = factory.LazyAttribute(lambda n: bool(random.randint(0, 1)))

    class Meta:
        model = SubTask


class TaskEventFactory(factory.DjangoModelFactory):
    start = factory.LazyAttribute(lambda n: timezone.now())
    end = factory.LazyAttribute(lambda n: n.start + timedelta(minutes=25))

    class Meta:
        model = TaskEvent
