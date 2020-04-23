import random
from datetime import timedelta

import factory
import pytest
from pytest_lazyfixture import lazy_fixture

from pomodorr.projects.serializers import ProjectSerializer, PrioritySerializer, TaskSerializer

pytestmark = pytest.mark.django_db


class TestPrioritySerializer:
    serializer_class = PrioritySerializer

    def test_serialize_many_priorities(self, priority_model, priority_create_batch):
        serializer = self.serializer_class(instance=priority_model.objects.all(), many=True)

        assert serializer.data is not None
        assert len(serializer.data) == 5
        assert 'user' in serializer.data[0].keys()

    def test_serialize_single_priority(self, priority_instance):
        serializer = self.serializer_class(instance=priority_instance)

        assert serializer.data is not None
        assert 'user' in serializer.data.keys()

    def test_save_priority_with_valid_data(self, priority_data, request_mock, active_user):
        request_mock.user = active_user

        serializer = self.serializer_class(data=priority_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid()
        assert all([value in serializer.validated_data for value in priority_data])

    @pytest.mark.parametrize(
        'invalid_field_key, invalid_field_value',
        [
            ('name', factory.Faker('pystr', max_chars=129).generate()),
            ('name', ''),
            ('priority_level', random.randint(-999, -1)),
            ('priority_level', ''),
            ('color', factory.Faker('pystr', max_chars=19).generate()),
            ('color', '')
        ]
    )
    def test_save_priority_with_invalid_data(self, invalid_field_key, invalid_field_value, request_mock, priority_data,
                                             active_user):
        request_mock.user = active_user
        priority_data[invalid_field_key] = invalid_field_value

        serializer = self.serializer_class(data=priority_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert invalid_field_key in serializer.errors

    def test_save_priority_with_unique_constraint_violated(self, request_mock, priority_data, priority_instance,
                                                           active_user):
        request_mock.user = active_user
        priority_data['name'] = priority_instance.name

        serializer = self.serializer_class(data=priority_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert 'Priority\'s name must be unique.' in serializer.errors['non_field_errors']

    def test_save_priority_without_context_user(self, priority_data):
        serializer = self.serializer_class(data=priority_data)

        with pytest.raises(KeyError):
            serializer.is_valid()

    def test_update_priority_with_valid_data(self, priority_data, priority_instance, request_mock, active_user):
        request_mock.user = active_user
        serializer = self.serializer_class(instance=priority_instance, data=priority_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid()
        assert all(value in serializer.validated_data for value in priority_data)

    @pytest.mark.parametrize(
        'invalid_field_key, invalid_field_value',
        [
            ('name', factory.Faker('pystr', max_chars=129).generate()),
            ('name', ''),
            ('priority_level', random.randint(-999, -1)),
            ('priority_level', ''),
            ('color', factory.Faker('pystr', max_chars=19).generate()),
            ('color', '')
        ]
    )
    def test_update_priority_with_invalid_data(self, invalid_field_key, invalid_field_value, priority_data,
                                               priority_instance, request_mock, active_user):
        request_mock.user = active_user
        priority_data[invalid_field_key] = invalid_field_value
        serializer = self.serializer_class(instance=priority_instance, data=priority_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert invalid_field_key in serializer.errors

    def test_update_priority_with_unique_constraint_violated(self, request_mock, priority_data, priority_instance,
                                                             priority_create_batch, active_user):
        request_mock.user = active_user
        priority_data['name'] = priority_create_batch[0].name

        serializer = self.serializer_class(data=priority_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert 'Priority\'s name must be unique.' in serializer.errors['non_field_errors']

    def test_update_priority_without_context_user(self, priority_data, priority_instance):
        serializer = self.serializer_class(instance=priority_instance, data=priority_data)

        with pytest.raises(KeyError):
            assert serializer.is_valid()


class TestProjectSerializer:
    serializer_class = ProjectSerializer

    def test_serialize_many_projects(self, project_model, project_create_batch):
        serializer = self.serializer_class(instance=project_model.objects.all(), many=True)

        assert serializer.data is not None
        assert len(serializer.data) == 5
        assert 'user' not in serializer.data[0].keys()

    def test_serialize_single_project(self, project_instance):
        serializer = self.serializer_class(instance=project_instance)

        assert serializer.data is not None
        assert 'user' not in serializer.data.keys()

    def test_save_project_with_valid_data(self, project_data, request_mock, active_user, priority_instance):
        project_data['priority'] = priority_instance.id
        request_mock.user = active_user
        serializer = self.serializer_class(data=project_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid()
        assert all(value in serializer.validated_data for value in project_data)

    @pytest.mark.parametrize(
        'invalid_field_key, invalid_field_value',
        [
            ('name', factory.Faker('pystr', max_chars=129).generate()),
            ('name', ''),
            ('priority', random.randint(-999, -1)),
            ('priority', lazy_fixture('random_priority_id')),
            ('user_defined_ordering', random.randint(-999, -1)),
            ('user_defined_ordering', '')
        ]
    )
    def test_save_project_with_invalid_data(self, invalid_field_key, invalid_field_value, project_data, request_mock,
                                            active_user):
        request_mock.user = active_user
        project_data[invalid_field_key] = invalid_field_value
        serializer = self.serializer_class(data=project_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert invalid_field_key in serializer.errors

    def test_save_project_with_unique_constraint_violated(self, project_data, project_instance, request_mock,
                                                          priority_instance, active_user):
        project_data['name'] = project_instance.name
        project_data['priority'] = priority_instance.id
        request_mock.user = active_user
        serializer = self.serializer_class(data=project_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert 'Project\'s name must be unique.' in serializer.errors['name']

    def test_save_project_without_context_user(self, project_data):
        serializer = self.serializer_class(data=project_data)

        with pytest.raises(KeyError):
            serializer.is_valid()

    def test_update_project_with_valid_data(self, project_data, project_instance, request_mock, priority_instance,
                                            active_user):
        project_data['priority'] = priority_instance.id
        request_mock.user = active_user
        serializer = self.serializer_class(instance=project_instance, data=project_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid()
        assert all(value in serializer.validated_data for value in project_data)

    @pytest.mark.parametrize(
        'invalid_field_key, invalid_field_value',
        [
            ('name', factory.Faker('pystr', max_chars=129).generate()),
            ('name', ''),
            ('priority', random.randint(-999, -1)),
            ('priority', lazy_fixture('random_priority_id')),
            ('user_defined_ordering', random.randint(-999, -1)),
            ('user_defined_ordering', '')
        ]
    )
    def test_update_project_with_invalid_data(self, invalid_field_key, invalid_field_value, project_data,
                                              project_instance, request_mock, active_user):
        project_data[invalid_field_key] = invalid_field_value
        request_mock.user = active_user
        serializer = self.serializer_class(instance=project_instance, data=project_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert invalid_field_key in serializer.errors

    def test_update_project_with_unique_constraint_violated(self, project_data, project_instance,
                                                            project_create_batch,
                                                            request_mock, priority_instance, active_user):
        project_data['name'] = project_create_batch[0].name
        project_data['priority'] = priority_instance.id
        request_mock.user = active_user
        serializer = self.serializer_class(instance=project_instance, data=project_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert 'Project\'s name must be unique.' in serializer.errors['name']

    def test_update_project_without_context_user(self, project_data, project_instance, ):
        serializer = self.serializer_class(instance=project_instance, data=project_data)

        with pytest.raises(KeyError):
            serializer.is_valid()


class TestTaskSerializer:
    serializer_class = TaskSerializer

    def test_serialize_many_tasks(self, task_model, task_instance, completed_task_instance):
        serializer = self.serializer_class(instance=task_model.objects.all(), many=True)

        assert serializer.data is not None
        assert len(serializer.data) == 2

    def test_serializer_single_task(self, task_instance):
        serializer = self.serializer_class(instance=task_instance)

        assert serializer.data is not None
        assert serializer.data['id'] == str(task_instance.id)

    def test_save_task_with_valid_data(self, task_data, request_mock, active_user, project_instance, priority_instance):
        task_data['project'] = project_instance.id
        task_data['priority'] = priority_instance.id
        request_mock.user = active_user

        serializer = self.serializer_class(data=task_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid()
        assert all(value in serializer.validated_data for value in task_data)

    @pytest.mark.parametrize(
        'invalid_field_key, invalid_field_value, get_field',
        [
            ('name', factory.Faker('pystr', max_chars=129).generate(), None),
            ('name', lazy_fixture('completed_task_instance'), 'name'),
            ('name', '', None),
            ('user_defined_ordering', random.randint(-999, -1), None),
            ('user_defined_ordering', '', None),
            ('pomodoro_number', '', None),
            ('priority', lazy_fixture('priority_instance_for_random_user'), 'id'),
            ('project', lazy_fixture('project_instance_for_random_user'), 'id'),
            ('project', '', None)
        ]
    )
    def test_save_task_with_invalid_data(self, invalid_field_key, invalid_field_value, get_field, task_data,
                                         request_mock, active_user, project_instance, priority_instance):
        task_data['project'] = project_instance.id
        task_data['priority'] = priority_instance.id
        request_mock.user = active_user

        if get_field is not None:
            task_data[invalid_field_key] = getattr(invalid_field_value, get_field)
        else:
            task_data[invalid_field_key] = invalid_field_value

        serializer = self.serializer_class(data=task_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert invalid_field_key in serializer.errors

    def test_update_task_with_valid_data(self, task_data, task_instance, priority_instance, project_instance,
                                         request_mock, active_user):
        task_data['project'] = project_instance.id
        task_data['priority'] = priority_instance.id
        request_mock.user = active_user

        serializer = self.serializer_class(instance=task_instance, data=task_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid()
        assert all(value in serializer.validated_data for value in task_data)

    @pytest.mark.parametrize(
        'invalid_field_key, invalid_field_value, get_field',
        [
            ('name', factory.Faker('pystr', max_chars=129).generate(), None),
            ('name', lazy_fixture('completed_task_instance'), 'name'),
            ('name', '', None),
            ('user_defined_ordering', random.randint(-999, -1), None),
            ('user_defined_ordering', '', None),
            ('pomodoro_number', '', None),
            ('priority', lazy_fixture('priority_instance_for_random_user'), 'id'),
            ('project', lazy_fixture('project_instance_for_random_user'), 'id'),
            ('project', '', None)
        ]
    )
    def test_update_task_with_invalid_data(self, invalid_field_key, invalid_field_value, get_field, task_data,
                                           task_instance, priority_instance, project_instance,
                                           request_mock, active_user):
        task_data['project'] = project_instance.id
        task_data['priority'] = priority_instance.id
        request_mock.user = active_user

        if get_field is not None:
            task_data[invalid_field_key] = getattr(invalid_field_value, get_field)
        else:
            task_data[invalid_field_key] = invalid_field_value

        serializer = self.serializer_class(instance=task_instance, data=task_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert invalid_field_key in serializer.errors

    @pytest.mark.parametrize(
        'changed_field, field_value',
        [
            ('name', 'xyz'),
            ('status', 1),
            ('priority', None),
            ('user_defined_ordering', 5),
            ('pomodoro_number', 14),
            ('pomodoro_length', timedelta(minutes=30)),
            ('due_date', None),
            ('reminder_date', None),
            ('repeat_duration', None),
        ]
    )
    def test_partial_update_task(self, changed_field, field_value, task_instance, request_mock, active_user):
        request_mock.user = active_user
        task_data = {
            changed_field: field_value
        }

        serializer = self.serializer_class(instance=task_instance, data=task_data, partial=True)
        serializer.context['request'] = request_mock

        assert serializer.is_valid()
        assert all(value in serializer.validated_data for value in task_data)
