import random
from datetime import timedelta

import factory
import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from pytest_lazyfixture import lazy_fixture

from pomodorr.projects.exceptions import TaskException, ProjectException, PriorityException, SubTaskException
from pomodorr.projects.selectors.task_selector import get_active_tasks
from pomodorr.projects.serializers import ProjectSerializer, PrioritySerializer, TaskSerializer, SubTaskSerializer
from pomodorr.tools.utils import get_time_delta

pytestmark = pytest.mark.django_db


class TestPrioritySerializer:
    serializer_class = PrioritySerializer

    def test_serialize_many_priorities(self, priority_model, priority_create_batch):
        serializer = self.serializer_class(instance=priority_model.objects.all(), many=True)

        assert serializer.data is not None
        assert len(serializer.data) == 5
        assert 'user' not in serializer.data[0].keys()

    def test_serialize_single_priority(self, priority_instance):
        serializer = self.serializer_class(instance=priority_instance)

        assert serializer.data is not None
        assert 'user' not in serializer.data.keys()

    def test_save_priority_with_valid_data(self, priority_data, request_mock):
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
        ]
    )
    def test_save_priority_with_invalid_data(self, invalid_field_key, invalid_field_value, request_mock, priority_data):
        priority_data[invalid_field_key] = invalid_field_value

        serializer = self.serializer_class(data=priority_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert invalid_field_key in serializer.errors

    def test_save_priority_with_unique_constraint_violated(self, request_mock, priority_data, priority_instance):
        priority_data['name'] = priority_instance.name

        serializer = self.serializer_class(data=priority_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert serializer.errors['name'][0] == PriorityException.messages[PriorityException.priority_duplicated]

    def test_save_priority_without_context_user(self, priority_data):
        serializer = self.serializer_class(data=priority_data)

        with pytest.raises(KeyError):
            serializer.is_valid()

    def test_update_priority_with_valid_data(self, priority_data, priority_instance, request_mock):
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
        ]
    )
    def test_update_priority_with_invalid_data(self, invalid_field_key, invalid_field_value, priority_data,
                                               priority_instance, request_mock):
        priority_data[invalid_field_key] = invalid_field_value
        serializer = self.serializer_class(instance=priority_instance, data=priority_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert invalid_field_key in serializer.errors

    def test_update_priority_with_unique_constraint_violated(self, request_mock, priority_data, priority_instance,
                                                             priority_create_batch):
        priority_data['name'] = priority_create_batch[0].name

        serializer = self.serializer_class(instance=priority_instance, data=priority_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert serializer.errors['name'][0] == PriorityException.messages[PriorityException.priority_duplicated]

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

    def test_save_project_with_valid_data(self, project_data, request_mock, priority_instance):
        project_data['priority'] = priority_instance.id

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
    def test_save_project_with_invalid_data(self, invalid_field_key, invalid_field_value, project_data, request_mock):
        project_data[invalid_field_key] = invalid_field_value
        serializer = self.serializer_class(data=project_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert invalid_field_key in serializer.errors

    def test_save_project_with_unique_constraint_violated(self, project_data, project_instance, request_mock,
                                                          priority_instance):
        project_data['name'] = project_instance.name
        project_data['priority'] = priority_instance.id

        serializer = self.serializer_class(data=project_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert serializer.errors['name'][0] == ProjectException.messages[ProjectException.project_duplicated]

    def test_save_project_without_context_user(self, project_data):
        serializer = self.serializer_class(data=project_data)

        with pytest.raises(KeyError):
            serializer.is_valid()

    def test_update_project_with_valid_data(self, project_data, project_instance, request_mock, priority_instance):
        project_data['priority'] = priority_instance.id

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
                                              project_instance, request_mock):
        project_data[invalid_field_key] = invalid_field_value

        serializer = self.serializer_class(instance=project_instance, data=project_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert invalid_field_key in serializer.errors

    def test_update_project_with_unique_constraint_violated(self, project_data, project_instance, project_create_batch,
                                                            request_mock, priority_instance):
        project_data['name'] = project_create_batch[0].name
        project_data['priority'] = priority_instance.id

        serializer = self.serializer_class(instance=project_instance, data=project_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert serializer.errors['name'][0] == ProjectException.messages[ProjectException.project_duplicated]

    def test_update_project_without_context_user(self, project_data, project_instance):
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

    def test_save_task_with_valid_data(self, task_data, request_mock, project_instance, priority_instance):
        task_data['project'] = project_instance.id
        task_data['priority'] = priority_instance.id

        serializer = self.serializer_class(data=task_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid()
        assert serializer.validated_data is not None

    @pytest.mark.parametrize(
        'invalid_field_key, invalid_field_value, get_field',
        [
            ('name', factory.Faker('pystr', max_chars=129).generate(), None),
            ('name', lazy_fixture('repeatable_task_instance'), 'name'),
            ('name', '', None),
            ('user_defined_ordering', random.randint(-999, -1), None),
            ('user_defined_ordering', '', None),
            ('pomodoro_number', 'xyz', None),
            ('pomodoro_number', '', None),
            ('repeat_duration', timedelta(minutes=5), None),
            ('repeat_duration', timedelta(days=5, minutes=5), None),
            ('due_date', get_time_delta({'days': 1}, ahead=False), None),
            ('due_date', get_time_delta({'days': 1}, ahead=False).strftime('%Y-%m-%d'), None),
            ('priority', lazy_fixture('priority_instance_for_random_user'), 'id'),
            ('project', lazy_fixture('project_instance_for_random_user'), 'id'),
            ('project', '', None),
            ('status', '', None),
            ('status', 3, None),
            ('status', 1, None)  # you can create only active tasks
        ]
    )
    def test_save_task_with_invalid_data(self, invalid_field_key, invalid_field_value, get_field, task_data,
                                         request_mock, project_instance, priority_instance):
        task_data['project'] = project_instance.id
        task_data['priority'] = priority_instance.id

        if get_field is not None:
            task_data[invalid_field_key] = getattr(invalid_field_value, get_field)
        else:
            task_data[invalid_field_key] = invalid_field_value

        serializer = self.serializer_class(data=task_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert invalid_field_key in serializer.errors

    def test_update_task_with_valid_data(self, task_data, task_instance, priority_instance, project_instance,
                                         request_mock):
        task_data['project'] = project_instance.id
        task_data['priority'] = priority_instance.id

        serializer = self.serializer_class(instance=task_instance, data=task_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid()
        assert serializer.validated_data is not None

    @pytest.mark.parametrize(
        'invalid_field_key, invalid_field_value, get_field',
        [
            ('name', factory.Faker('pystr', max_chars=129).generate(), None),
            ('name', lazy_fixture('repeatable_task_instance'), 'name'),
            ('name', '', None),
            ('user_defined_ordering', random.randint(-999, -1), None),
            ('user_defined_ordering', '', None),
            ('pomodoro_number', 'xyz', None),
            ('pomodoro_number', '', None),
            ('repeat_duration', timedelta(minutes=5), None),
            ('repeat_duration', timedelta(days=5, minutes=5), None),
            ('due_date', get_time_delta({'days': 1}, ahead=False), None),
            ('due_date', get_time_delta({'days': 1}, ahead=False).strftime('%Y-%m-%d'), None),
            ('priority', lazy_fixture('priority_instance_for_random_user'), 'id'),
            ('project', lazy_fixture('project_instance_for_random_user'), 'id'),
            ('project', '', None),
            ('status', '', None),
            ('status', 3, None)
        ]
    )
    def test_update_task_with_invalid_data(self, invalid_field_key, invalid_field_value, get_field, task_data,
                                           task_instance, priority_instance, project_instance,
                                           request_mock):
        task_data['project'] = project_instance.id
        task_data['priority'] = priority_instance.id

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
            ('due_date', get_time_delta({'days': 1})),
            ('due_date', None),
            ('reminder_date', None),
            ('repeat_duration', None),
        ]
    )
    def test_partial_update_task(self, changed_field, field_value, task_instance, request_mock):
        task_data = {
            changed_field: field_value
        }

        serializer = self.serializer_class(instance=task_instance, data=task_data, partial=True)
        serializer.context['request'] = request_mock

        assert serializer.is_valid()
        assert all(value in serializer.validated_data for value in task_data)

    def test_pin_task_to_new_project_with_unique_name_for_new_project(self, task_instance, project_create_batch,
                                                                      request_mock):
        new_project = project_create_batch[0]

        task_data = {
            'project': new_project.id
        }

        serializer = self.serializer_class(instance=task_instance, data=task_data, partial=True)
        serializer.context['request'] = request_mock
        assert serializer.is_valid()

        pinned_task = serializer.save()
        assert pinned_task.project == new_project

    def test_pin_task_to_new_project_with_colliding_name_for_new_project(self, task_instance, request_mock,
                                                                         duplicate_task_instance_in_second_project):
        new_project = duplicate_task_instance_in_second_project.project

        task_data = {
            'project': new_project.id
        }

        serializer = self.serializer_class(instance=task_instance, data=task_data, partial=True)
        serializer.context['request'] = request_mock

        assert serializer.is_valid()
        with pytest.raises(ValidationError) as exc:
            serializer.save()

        assert exc.value.messages[0] == TaskException.messages[TaskException.task_duplicated]

    def test_complete_one_time_task(self, task_model, task_instance, request_mock):
        task_data = {
            'status': task_model.status_completed
        }

        serializer = self.serializer_class(instance=task_instance, data=task_data, partial=True)
        serializer.context['request'] = request_mock

        assert serializer.is_valid()
        completed_task = serializer.save()
        assert completed_task.status == task_model.status_completed

    def test_complete_repeatable_task_create_new_task_for_next_due_date(self, task_model, request_mock,
                                                                        repeatable_task_instance_without_due_date):
        task_data = {
            'status': task_model.status_completed
        }

        serializer = self.serializer_class(instance=repeatable_task_instance_without_due_date, data=task_data,
                                           partial=True)
        serializer.context['request'] = request_mock

        assert serializer.is_valid()
        completed_task = serializer.save()
        assert completed_task.status == task_model.status_completed

        next_task = get_active_tasks(project=completed_task.project, name=completed_task.name)[0]
        assert next_task.due_date is not None and next_task.due_date.date() == timezone.now().date()

    def test_complete_task_force_finishes_current_pomodoros(self, task_model, task_instance, date_frame_in_progress,
                                                            request_mock):
        task_data = {
            'status': task_model.status_completed
        }
        serializer = self.serializer_class(instance=task_instance, data=task_data, partial=True)
        serializer.context['request'] = request_mock

        assert date_frame_in_progress.end is None
        assert serializer.is_valid()
        completed_task = serializer.save()

        date_frame_in_progress.refresh_from_db()
        assert completed_task.status == task_model.status_completed
        assert date_frame_in_progress.end is not None

    @pytest.mark.parametrize(
        'completed_task',
        [
            lazy_fixture('completed_task_instance'),
            lazy_fixture('completed_repeatable_task_instance')
        ]
    )
    def test_reactivate_task(self, completed_task, task_model, request_mock):
        task_data = {
            'status': task_model.status_active
        }
        serializer = self.serializer_class(instance=completed_task, data=task_data, partial=True)
        serializer.context['request'] = request_mock

        assert serializer.is_valid()
        reactivated_task = serializer.save()

        assert reactivated_task.status == task_model.status_active

    @pytest.mark.parametrize(
        'completed_task',
        [
            lazy_fixture('completed_task_instance'),
            lazy_fixture('completed_repeatable_task_instance')
        ]
    )
    def test_reactivate_task_with_existing_active_duplicate(self, completed_task, task_model, task_instance,
                                                            request_mock):
        task_instance.name = completed_task.name
        task_instance.save()

        task_data = {
            'status': task_model.status_active
        }
        serializer = self.serializer_class(instance=completed_task, data=task_data, partial=True)
        serializer.context['request'] = request_mock

        assert serializer.is_valid()
        with pytest.raises(ValidationError) as exc:
            serializer.save()

        assert exc.value.messages[0] == TaskException.messages[TaskException.task_duplicated]


class TestSubTaskSerializer:
    serializer_class = SubTaskSerializer

    def test_serialize_many_sub_tasks(self, sub_task_model, sub_task_create_batch):
        serializer = self.serializer_class(instance=sub_task_model.objects.all(), many=True)

        assert serializer is not None
        assert len(serializer.data) == 5

    def test_serializer_single_sub_task(self, sub_task_instance):
        serializer = self.serializer_class(instance=sub_task_instance)

        assert serializer.data is not None
        assert all(key in serializer.data.keys() for key in self.serializer_class.Meta.fields)

    def test_save_sub_task_with_valid_data(self, sub_task_data, task_instance, request_mock):
        sub_task_data['task'] = task_instance.id
        serializer = self.serializer_class(data=sub_task_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid()
        sub_task = serializer.save()

        assert sub_task is not None
        assert sub_task.task == task_instance

    @pytest.mark.parametrize(
        'invalid_field_key, invalid_field_value, get_field',
        [
            ('name', factory.Faker('pystr', max_chars=129).generate(), None),
            ('name', '', None),
            ('name', None, None),
            ('task', lazy_fixture('task_instance_for_random_project'), 'id'),
            ('task', '', None),
            ('task', None, None),
            ('is_completed', '', None),
            ('is_completed', None, None),
            ('is_completed', 123, None),
            ('is_completed', 'xyz', None),
        ]
    )
    def test_save_sub_task_with_invalid_data(self, invalid_field_key, invalid_field_value, get_field, sub_task_data,
                                             task_instance, request_mock):
        sub_task_data['task'] = task_instance.id
        if get_field is not None:
            sub_task_data[invalid_field_key] = getattr(invalid_field_value, get_field)
        else:
            sub_task_data[invalid_field_key] = invalid_field_value

        serializer = self.serializer_class(data=sub_task_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert invalid_field_key in serializer.errors.keys()

    def test_save_sub_task_with_unique_constraint_violated(self, sub_task_data, task_instance, sub_task_create_batch,
                                                           request_mock):

        sub_task_data['task'] = task_instance.id
        sub_task_data['name'] = sub_task_create_batch[0].name

        serializer = self.serializer_class(data=sub_task_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert serializer.errors['name'][0] == SubTaskException.messages[SubTaskException.sub_task_duplicated]

    def test_save_sub_task_with_completed_task_returns_error(self, sub_task_data, completed_task_instance,
                                                             request_mock):
        sub_task_data['task'] = completed_task_instance.id
        serializer = self.serializer_class(data=sub_task_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert serializer.errors['task'][0] == SubTaskException.messages[SubTaskException.task_already_completed]

    def test_update_sub_task_with_valid_data(self, sub_task_data, sub_task_instance, task_instance, request_mock):
        sub_task_data['task'] = task_instance.id
        serializer = self.serializer_class(instance=sub_task_instance, data=sub_task_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is True
        assert all(key in serializer.validated_data for key in sub_task_data.keys())

    @pytest.mark.parametrize(
        'invalid_field_key, invalid_field_value, get_field',
        [
            ('name', factory.Faker('pystr', max_chars=129).generate(), None),
            ('name', '', None),
            ('name', None, None),
            ('task', lazy_fixture('task_instance_for_random_project'), 'id'),
            ('task', '', None),
            ('task', None, None),
            ('is_completed', '', None),
            ('is_completed', None, None),
            ('is_completed', 123, None),
            ('is_completed', 'xyz', None),
        ]
    )
    def test_update_sub_task_with_invalid_data(self, invalid_field_key, invalid_field_value, get_field, sub_task_data,
                                               sub_task_instance, task_instance, request_mock):
        sub_task_data['task'] = task_instance.id
        if get_field is not None:
            sub_task_data[invalid_field_key] = getattr(invalid_field_value, get_field)
        else:
            sub_task_data[invalid_field_key] = invalid_field_value

        serializer = self.serializer_class(instance=sub_task_instance, data=sub_task_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert invalid_field_key in serializer.errors.keys()

    def test_update_sub_task_with_unique_constraint_violated(self, sub_task_data, sub_task_instance, task_instance,
                                                             sub_task_create_batch, request_mock):
        sub_task_data['task'] = task_instance.id
        sub_task_data['name'] = sub_task_create_batch[0].name

        serializer = self.serializer_class(instance=sub_task_instance, data=sub_task_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert serializer.errors['name'][0] == SubTaskException.messages[SubTaskException.sub_task_duplicated]

    def test_update_sub_task_doesnt_allow_task_change(self, sub_task_data, sub_task_instance, task_instance,
                                                      repeatable_task_instance, request_mock):
        sub_task_data['task'] = repeatable_task_instance.id
        serializer = self.serializer_class(instance=sub_task_instance, data=sub_task_data)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert serializer.errors['task'][0] == SubTaskException.messages[SubTaskException.cannot_change_task]

    @pytest.mark.parametrize(
        'changed_field, field_value',
        [
            ('name', 'xyz'),
            ('is_completed', False),
            ('is_completed', True),
        ]
    )
    def test_update_partial_sub_task(self, changed_field, field_value, sub_task_instance, task_instance, request_mock):
        sub_task_data = {changed_field: field_value, 'task': task_instance.id}

        serializer = self.serializer_class(instance=sub_task_instance, data=sub_task_data, partial=True)
        serializer.context['request'] = request_mock

        assert serializer.is_valid()
        assert serializer.validated_data[changed_field] == field_value

    def test_update_partial_sub_task_doesnt_allow_task_change(self, sub_task_instance, task_instance,
                                                              repeatable_task_instance, request_mock):
        sub_task_data = {
            'task': repeatable_task_instance.id
        }

        serializer = self.serializer_class(instance=sub_task_instance, data=sub_task_data, partial=True)
        serializer.context['request'] = request_mock

        assert serializer.is_valid() is False
        assert serializer.errors['task'][0] == SubTaskException.messages[SubTaskException.cannot_change_task]
