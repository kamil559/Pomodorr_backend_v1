import random

import factory
import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

pytestmark = pytest.mark.django_db(transaction=True)


def test_create_project_model_with_valid_data(project_model, project_data, active_user):
    project = project_model.objects.create(user=active_user, **project_data)

    assert project is not None
    assert project.user == active_user


@pytest.mark.parametrize(
    'invalid_field_key, invalid_field_value, expected_exception',
    [
        ('name', factory.Faker('pystr', max_chars=129).generate(), ValidationError),
        ('name', '', ValidationError),
        ('user_defined_ordering', random.randint(-999, -1), IntegrityError),
        ('user_defined_ordering', '', ValueError),
        ('user', None, IntegrityError)
    ]
)
def test_create_project_model_with_invalid_data(invalid_field_key, invalid_field_value, expected_exception,
                                                project_model, project_data, active_user):
    project_data['user'] = active_user
    project_data[invalid_field_key] = invalid_field_value

    with pytest.raises(expected_exception):
        project = project_model.objects.create(**project_data)
        project.full_clean()


def test_create_project_duplicate_for_one_user(project_model, project_data, project_instance, active_user):
    project_data['name'], project_data['user'] = project_instance.name, active_user

    with pytest.raises(IntegrityError):
        project = project_model.objects.create(**project_data)
        project.full_clean()


def test_project_soft_delete(project_model, project_instance):
    project_instance.delete()

    assert project_instance.id is not None
    assert project_instance not in project_model.objects.all()
    assert project_instance in project_model.all_objects.filter()


def test_project_hard_delete(project_model, project_instance):
    project_instance.delete(soft=False)

    assert project_instance.id is None
    assert project_instance not in project_model.objects.all()
    assert project_instance not in project_model.all_objects.filter()
