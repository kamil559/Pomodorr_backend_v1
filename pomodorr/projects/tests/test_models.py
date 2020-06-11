import random
from datetime import timedelta

import factory
import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

pytestmark = pytest.mark.django_db(transaction=True)


class TestProjectModel:
    def test_create_project_model_with_valid_data(self, project_model, project_data, active_user):
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
    def test_create_project_model_with_invalid_data(self, invalid_field_key, invalid_field_value, expected_exception,
                                                    project_model, project_data, active_user):
        project_data['user'] = active_user
        project_data[invalid_field_key] = invalid_field_value

        with pytest.raises(expected_exception):
            project = project_model.objects.create(**project_data)
            project.full_clean()

    def test_create_project_with_unique_constraint_violated(self, project_model, project_data, project_instance,
                                                            active_user):
        project_data['name'], project_data['user'] = project_instance.name, active_user

        with pytest.raises(IntegrityError) as exc:
            project = project_model.objects.create(**project_data)
            project.full_clean()

        assert str(exc.value) == 'UNIQUE constraint failed: projects_project.name, projects_project.user_id'

    def test_project_soft_delete(self, project_model, project_instance):
        project_instance.delete()

        assert project_instance.id is not None
        assert project_instance not in project_model.objects.all()
        assert project_instance in project_model.all_objects.filter()

    def test_project_hard_delete(self, project_model, project_instance):
        project_instance.delete(soft=False)

        assert project_instance.id is None
        assert project_instance not in project_model.objects.all()
        assert project_instance not in project_model.all_objects.filter()


class TestPriorityModel:
    def test_create_priority_with_valid_data(self, priority_model, priority_data, active_user):
        priority = priority_model.objects.create(user=active_user, **priority_data)

        assert priority is not None
        assert priority.user == active_user

    @pytest.mark.parametrize(
        'invalid_field_key, invalid_field_value, expected_exception',
        [
            ('name', factory.Faker('pystr', max_chars=129).generate(), ValidationError),
            ('name', '', ValidationError),
            ('priority_level', random.randint(-999, -1), IntegrityError),
            ('priority_level', '', ValueError),
            ('color', factory.Faker('pystr', max_chars=19).generate(), ValidationError),
            ('user', None, IntegrityError)
        ]
    )
    def test_create_priority_with_invalid_data(self, invalid_field_key, invalid_field_value, expected_exception,
                                               priority_model, priority_data, active_user):
        priority_data['user'] = active_user
        priority_data[invalid_field_key] = invalid_field_value

        with pytest.raises(expected_exception):
            priority = priority_model.objects.create(**priority_data)
            priority.full_clean()

    def test_create_priority_with_unique_constraint_violated(self, priority_model, priority_data, priority_instance,
                                                             active_user):
        priority_data['name'], priority_data['user'] = priority_instance.name, active_user

        with pytest.raises(IntegrityError) as exc:
            priority = priority_model.objects.create(**priority_data)
            priority.full_clean()

        assert str(exc.value) == 'UNIQUE constraint failed: projects_priority.name, projects_priority.user_id'


class TestTaskModel:
    def test_create_task_with_valid_data(self, task_model, task_data, priority_instance, project_instance):
        task = task_model.objects.create(priority=priority_instance, project=project_instance, **task_data)

        assert task is not None
        assert task.priority == priority_instance
        assert task.project == project_instance

    @pytest.mark.parametrize(
        'invalid_field_key, invalid_field_value, expected_exception',
        [
            ('name', factory.Faker('pystr', max_chars=129).generate(), ValidationError),
            ('name', '', ValidationError),
            ('user_defined_ordering', random.randint(-999, -1), IntegrityError),
            ('user_defined_ordering', '', ValueError),
            ('pomodoro_number', '', ValueError),
            ('project', None, IntegrityError)
        ]
    )
    def test_create_task_with_invalid_data(self, invalid_field_key, invalid_field_value, expected_exception, task_model,
                                           task_data, priority_instance, project_instance):
        task_data['priority'], task_data['project'] = priority_instance, project_instance
        task_data[invalid_field_key] = invalid_field_value

        with pytest.raises(expected_exception):
            task = task_model.objects.create(**task_data)
            task.full_clean()

    def test_create_task_with_unique_constraint(self, task_model, task_data, task_instance, priority_instance,
                                                project_instance):
        task_data['name'] = task_instance.name

        with pytest.raises(IntegrityError) as exc:
            task = task_model.objects.create(priority=priority_instance, project=project_instance, **task_data)
            task.full_clean()
        assert str(exc.value) == 'UNIQUE constraint failed: projects_task.name, projects_task.project_id'

    def test_task_soft_delete(self, task_model, task_instance):
        task_instance.delete()

        assert task_instance.id is not None
        assert task_instance not in task_model.objects.all()
        assert task_instance in task_model.all_objects.filter()

    def test_task_hard_delete(self, task_model, task_instance):
        task_instance.delete(soft=False)

        assert task_instance.id is None
        assert task_instance not in task_model.objects.all()
        assert task_instance not in task_model.all_objects.all()

    def test_normalized_pomodoro_length_for_task_with_pomodoro_length(self, task_instance):
        assert task_instance.normalized_pomodoro_length == timedelta(minutes=50)

    def test_normalized_pomodoro_length_for_task_without_pomodoro_length(self, task_instance_without_lengths):
        assert task_instance_without_lengths.normalized_pomodoro_length == timedelta(minutes=25)

    def test_normalized_break_length_for_task_with_break_length(self, task_instance):
        assert task_instance.normalized_break_length == timedelta(minutes=30)

    def test_normalized_break_length_for_task_without_break_length(self, task_instance_without_lengths):
        assert task_instance_without_lengths.normalized_break_length == timedelta(minutes=5)


class TestSubTask:
    def test_create_sub_task_with_valid_data(self, sub_task_model, sub_task_data, task_instance):
        sub_task = sub_task_model.objects.create(task=task_instance, **sub_task_data)

        assert sub_task is not None
        assert sub_task.task == task_instance

    @pytest.mark.parametrize(
        'invalid_field_key, invalid_field_value, expected_exception',
        [
            ('name', factory.Faker('pystr', max_chars=129).generate(), ValidationError),
            ('name', '', ValidationError),
            ('task', None, ValidationError),
            ('is_completed', '', ValidationError)
        ]
    )
    def test_create_sub_task_with_invalid_data(self, invalid_field_key, invalid_field_value, expected_exception,
                                               sub_task_model, sub_task_data, task_instance):
        sub_task_data['task'] = task_instance
        sub_task_data[invalid_field_key] = invalid_field_value

        with pytest.raises(expected_exception):
            sub_task = sub_task_model(**sub_task_data)
            sub_task.full_clean()

    def test_create_sub_task_with_unique_constraint_violated(self, sub_task_model, sub_task_data, task_instance,
                                                             sub_task_instance):
        sub_task_data['name'] = sub_task_instance.name

        with pytest.raises(IntegrityError) as exc:
            sub_task = sub_task_model.objects.create(task=task_instance, **sub_task_data)
            sub_task.full_clean()

        assert str(exc.value) == 'UNIQUE constraint failed: projects_subtask.name, projects_subtask.task_id'
