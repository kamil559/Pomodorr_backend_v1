import random
import factory

from pomodorr.projects.models import Project, Priority


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
    repeat_duration = factory.LazyAttribute(lambda n: f'{random.randint(1, 20)} 0:0:0.0')
    note = factory.Faker('text')


class SubTaskFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: f'SubTask {n}')
