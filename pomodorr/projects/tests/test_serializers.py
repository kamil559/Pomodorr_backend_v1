import random
import factory
import pytest
from rest_framework.exceptions import ValidationError

from pomodorr.projects.serializers import ProjectSerializer

pytestmark = pytest.mark.django_db


def test_serializer_many_projects(project_model, project_create_batch):
    serializer = ProjectSerializer(instance=project_model.objects.all(), many=True)

    assert serializer.data is not None
    assert len(serializer.data) == 5
    assert 'user' not in dict(serializer.data[0]).keys()


def test_serializer_single_project(project_instance):
    serializer = ProjectSerializer(instance=project_instance)

    assert serializer.data is not None
    assert 'user' not in dict(serializer.data).keys()


def test_serializer_save_with_valid_data(project_data, request_mock, active_user):
    request_mock.user = active_user
    serializer = ProjectSerializer(data=project_data)
    serializer.context['request'] = request_mock

    assert serializer.is_valid() is True
    assert all([value in serializer.validated_data for value in project_data])


@pytest.mark.parametrize(
    'invalid_field_key, invalid_field_value, expected_exception',
    [
        ('name', factory.Faker('pystr', max_chars=129).generate(), ValidationError),
        ('name', '', ValidationError),
        ('color', factory.Faker('pystr', max_chars=19).generate(), ValidationError),
        ('color', '', ValidationError),
        ('priority', random.randint(-999, -1), ValidationError),
        ('priority', '', ValidationError),
        ('user_defined_ordering', random.randint(-999, -1), ValidationError),
        ('user_defined_ordering', '', ValidationError)
    ]
)
def test_serializer_save_with_invalid_data(invalid_field_key, invalid_field_value, expected_exception, project_data,
                                           request_mock, active_user):
    request_mock.user = active_user
    project_data[invalid_field_key] = invalid_field_value
    serializer = ProjectSerializer(data=project_data)
    serializer.context['request'] = request_mock

    assert serializer.is_valid() is False
    assert invalid_field_key in serializer.errors


def test_serializer_save_with_unique_constraint_violated(project_data, project_instance, request_mock, active_user):
    project_data['name'] = project_instance.name
    request_mock.user = active_user
    serializer = ProjectSerializer(data=project_data)
    serializer.context['request'] = request_mock

    assert serializer.is_valid() is False
    assert 'The fields name, user must make a unique set.' in serializer.errors['non_field_errors']


def test_serializer_save_without_context_user(project_data):
    serializer = ProjectSerializer(data=project_data)

    with pytest.raises(KeyError):
        serializer.is_valid()


def test_serializer_update_with_valid_data(project_data, project_instance, request_mock, active_user):
    request_mock.user = active_user
    serializer = ProjectSerializer(instance=project_instance, data=project_data)
    serializer.context['request'] = request_mock

    assert serializer.is_valid() is True
    assert all([value in serializer.validated_data for value in project_data])


@pytest.mark.parametrize(
    'invalid_field_key, invalid_field_value, expected_exception',
    [
        ('name', factory.Faker('pystr', max_chars=129).generate(), ValidationError),
        ('name', '', ValidationError),
        ('color', factory.Faker('pystr', max_chars=19).generate(), ValidationError),
        ('color', '', ValidationError),
        ('priority', random.randint(-999, -1), ValidationError),
        ('priority', '', ValidationError),
        ('user_defined_ordering', random.randint(-999, -1), ValidationError),
        ('user_defined_ordering', '', ValidationError)
    ]
)
def test_serializer_update_with_invalid_data(invalid_field_key, invalid_field_value, expected_exception, project_data,
                                             project_instance, request_mock, active_user):
    project_data[invalid_field_key] = invalid_field_value
    request_mock.user = active_user
    serializer = ProjectSerializer(instance=project_instance, data=project_data)
    serializer.context['request'] = request_mock

    assert serializer.is_valid() is False
    assert invalid_field_key in serializer.errors


def test_serializer_update_with_unique_constraint_violated(project_data, project_instance, project_create_batch,
                                                           request_mock, active_user):
    project_data['name'] = project_create_batch[0].name
    request_mock.user = active_user
    serializer = ProjectSerializer(instance=project_instance, data=project_data)
    serializer.context['request'] = request_mock

    assert serializer.is_valid() is False
    assert 'The fields name, user must make a unique set.' in serializer.errors['non_field_errors']


def test_serializer_update_without_context_user(project_data, project_instance, ):
    serializer = ProjectSerializer(instance=project_instance, data=project_data)

    with pytest.raises(KeyError):
        serializer.is_valid()