import random
import factory

from pomodorr.projects.models import Project


class ProjectFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: f'Project number: {n}')
    color = factory.Faker('color')
    priority = factory.LazyAttribute(lambda x: random.randint(1, 50))
    user_defined_ordering = factory.LazyAttribute(lambda x: random.randint(1, 50))

    class Meta:
        model = Project
