import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from pomodorr.projects.exceptions import TaskException

pytestmark = pytest.mark.django_db


class TestProjectService:
    def test_check_project_name_is_available(self, project_service_model, project_data, active_user):
        checked_name = project_data['name']
        is_name_available = project_service_model.is_project_name_available(user=active_user,
                                                                            name=checked_name)

        assert is_name_available is True

    def test_check_project_name_is_not_available(self, project_service_model, project_instance, active_user):
        checked_name = project_instance.name
        is_name_available = project_service_model.is_project_name_available(user=active_user,
                                                                            name=checked_name)

        assert is_name_available is False

    def test_test_check_project_name_is_available_with_exclude_id(self, project_service_model, project_instance,
                                                                  active_user):
        checked_name = project_instance.name
        is_name_available = project_service_model.is_project_name_available(user=active_user,
                                                                            name=checked_name,
                                                                            exclude=project_instance)

        assert is_name_available is True


class TestTaskService:
    def test_check_task_name_is_available(self, task_service_model, task_data, project_instance):
        checked_name = task_data['name']
        is_name_available = task_service_model.is_task_name_available(project=project_instance,
                                                                      name=checked_name)

        assert is_name_available is True

    def test_check_task_name_is_not_available(self, task_service_model, task_instance, project_instance):
        checked_name = task_instance.name
        is_name_available = task_service_model.is_task_name_available(project=project_instance,
                                                                      name=checked_name)

        assert is_name_available is False

    def test_check_task_name_is_available_with_exclude_id(self, task_service_model, task_instance, project_instance):
        checked_name = task_instance.name
        is_name_available = task_service_model.is_task_name_available(project=project_instance,
                                                                      name=checked_name,
                                                                      exclude=task_instance)

        assert is_name_available is True

    def test_pin_task_to_new_project_with_unique_name_for_new_project(self, task_service_model, second_project_instance,
                                                                      task_instance, date_frame_create_batch):
        updated_task = task_service_model.pin_to_project(task=task_instance, project=second_project_instance)

        assert updated_task.project is second_project_instance

    def test_pin_task_to_new_project_with_colliding_name_for_new_project(
        self, task_service_model, task_instance, duplicate_task_instance_in_second_project):
        new_project = duplicate_task_instance_in_second_project.project

        with pytest.raises(ValidationError) as exc:
            task_service_model.pin_to_project(task=task_instance, project=new_project)

        assert exc.value.messages[0] == TaskException.messages[TaskException.task_duplicated]

    def test_complete_repeatable_task_creates_new_one_for_next_due_date(self, task_model, task_service_model,
                                                                        task_selector, repeatable_task_instance):
        completed_task = task_service_model.complete_task(task=repeatable_task_instance)
        expected_next_due_date = repeatable_task_instance.due_date + repeatable_task_instance.repeat_duration
        assert completed_task.status == task_model.status_completed
        next_task = task_selector.get_active_tasks(project=completed_task.project, name=completed_task.name)[0]

        assert next_task.status == task_model.status_active
        assert next_task.due_date.date() == expected_next_due_date.date()

    def test_complete_repeatable_task_without_due_date_sets_today_for_next_date_frame(
        self, task_model, task_service_model, task_selector, repeatable_task_instance_without_due_date):
        completed_task = task_service_model.complete_task(task=repeatable_task_instance_without_due_date)

        assert repeatable_task_instance_without_due_date.status == task_model.status_completed

        next_task = task_selector.get_active_tasks(project=completed_task.project, name=completed_task.name)[0]

        assert next_task.status == task_model.status_active
        assert next_task.due_date.date() == timezone.now().date()

    def test_complete_one_time_task_changes_status_to_completed(self, task_model, task_service_model, task_instance):
        task_service_model.complete_task(task=task_instance)

        assert task_instance.status == task_model.status_completed

    def test_mark_already_completed_one_time_task_as_completed_throws_error(self, task_service_model,
                                                                            completed_task_instance):
        with pytest.raises(ValidationError) as exc:
            task_service_model.complete_task(completed_task_instance)

        assert exc.value.messages[0] == TaskException.messages[TaskException.already_completed]

    def test_mark_task_as_completed_saves_pomodoro_in_progress_state(self, task_service_model, task_instance,
                                                                     date_frame_in_progress):
        assert date_frame_in_progress.start is not None and date_frame_in_progress.end is None
        task_service_model.complete_task(task=task_instance)
        date_frame_in_progress.refresh_from_db()

        assert date_frame_in_progress.end is not None

    def test_reactivate_one_time_task(self, task_model, task_service_model, completed_task_instance):
        task_service_model.reactivate_task(task=completed_task_instance)

        completed_task_instance.refresh_from_db()

        assert completed_task_instance.status == task_model.status_active

    def test_reactivate_one_time_task_with_existing_active_duplicate(self, task_service_model, task_instance,
                                                                     completed_task_instance):
        task_instance.name = completed_task_instance.name
        task_instance.save()

        with pytest.raises(ValidationError) as exc:
            task_service_model.reactivate_task(task=completed_task_instance)
        assert exc.value.messages[0] == TaskException.messages[TaskException.task_duplicated]

    def test_reactivate_repeatable_task(self, task_model, task_service_model, completed_repeatable_task_instance):
        task_service_model.reactivate_task(task=completed_repeatable_task_instance)

        completed_repeatable_task_instance.refresh_from_db()

        assert completed_repeatable_task_instance.status == task_model.status_active

    def test_reactivate_repeatable_task_with_existing_active_duplicate(self, task_service_model, task_instance,
                                                                       completed_repeatable_task_instance):
        task_instance.name = completed_repeatable_task_instance.name
        task_instance.save()

        with pytest.raises(ValidationError) as exc:
            task_service_model.reactivate_task(task=completed_repeatable_task_instance)
        assert exc.value.messages[0] == TaskException.messages[TaskException.task_duplicated]


class TestSubTaskService:
    def test_check_sub_task_name_is_available(self, sub_task_service_model, sub_task_data, task_instance):
        checked_name = sub_task_data['name']
        is_name_available = sub_task_service_model.is_sub_task_name_available(task=task_instance, name=checked_name)

        assert is_name_available is True

    def test_check_sub_task_name_is_not_available(self, sub_task_service_model, task_instance, sub_task_instance):
        checked_name = sub_task_instance.name
        is_name_available = sub_task_service_model.is_sub_task_name_available(task=task_instance, name=checked_name)

        assert is_name_available is False

    def test_check_sub_task_name_is_available_with_exclude_id(self, sub_task_service_model, task_instance,
                                                              sub_task_instance):
        checked_name = sub_task_instance.name
        is_name_available = sub_task_service_model.is_sub_task_name_available(task=task_instance, name=checked_name,
                                                                              exclude=sub_task_instance)

        assert is_name_available is True
