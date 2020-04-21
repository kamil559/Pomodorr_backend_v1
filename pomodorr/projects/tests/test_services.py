import pytest
from django.utils import timezone

from pomodorr.projects.exceptions import TaskException
from pomodorr.projects.services import ProjectServiceModel

pytestmark = pytest.mark.django_db


class TestProjectService:
    def test_check_project_name_is_available(self, project_data, active_user):
        checked_name = project_data['name']
        is_name_available = ProjectServiceModel.is_project_name_available(user=active_user,
                                                                          name=checked_name)

        assert is_name_available is True

    def test_check_project_name_is_not_available(self, project_instance, active_user):
        checked_name = project_instance.name
        is_name_available = ProjectServiceModel.is_project_name_available(user=active_user,
                                                                          name=checked_name)

        assert is_name_available is False

    def test_test_check_project_name_is_available_with_exclude_id(self, project_instance, active_user):
        checked_name = project_instance.name
        is_name_available = ProjectServiceModel.is_project_name_available(user=active_user,
                                                                          name=checked_name,
                                                                          exclude_id=project_instance.id)

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
                                                                      exclude_id=task_instance.id)

        assert is_name_available is True

    def test_pin_task_with_statistics_preserved_to_new_project_with_unique_name(self, task_service_model,
                                                                                second_project_instance, task_instance,
                                                                                task_event_create_batch):
        updated_task = task_service_model.pin_to_project(task=task_instance, project=second_project_instance,
                                                         preserve_statistics=True)
        assert task_instance.is_removed is True
        assert all(task_event.task is task_instance for task_event in task_event_create_batch)
        assert updated_task.project is second_project_instance
        assert updated_task.events.exists() is False

    def test_pin_task_with_statistics_preserved_to_new_project_with_colliding_name(
        self, task_service_model, second_project_instance, task_instance, duplicate_task_instance_in_second_project):
        assert task_instance.name == duplicate_task_instance_in_second_project.name
        assert task_instance.project is not duplicate_task_instance_in_second_project.project

        with pytest.raises(TaskException):
            task_service_model.pin_to_project(task=task_instance, project=second_project_instance,
                                              preserve_statistics=True)

    def test_simple_pin_task_to_new_project_with_unique_name_for_new_project(self, task_service_model,
                                                                             second_project_instance, task_instance,
                                                                             task_event_create_batch):
        updated_task = task_service_model.pin_to_project(task=task_instance, project=second_project_instance,
                                                         preserve_statistics=False)

        assert updated_task.project is second_project_instance
        assert all(task_event.task is updated_task for task_event in task_event_create_batch)

    def test_simple_pin_task_to_new_project_with_colliding_name_for_new_project(
        self, task_service_model, second_project_instance, task_instance, duplicate_task_instance_in_second_project):
        assert task_instance.name == duplicate_task_instance_in_second_project.name
        assert task_instance.project is not duplicate_task_instance_in_second_project.project
        with pytest.raises(TaskException):
            task_service_model.pin_to_project(task=task_instance, project=second_project_instance,
                                              preserve_statistics=False)

    def test_complete_repeatable_task_increments_due_date(self, task_model, task_service_model,
                                                          repeatable_task_instance):
        expected_next_due_date = repeatable_task_instance.due_date + repeatable_task_instance.repeat_duration
        task_service_model.complete_task(task=repeatable_task_instance)

        assert repeatable_task_instance.status == task_model.status_active
        assert repeatable_task_instance.due_date == expected_next_due_date

    def test_complete_repeatable_task_without_due_date_sets_today_as_due_date(self, task_model, task_service_model,
                                                                              repeatable_task_instance_without_due_date):
        expected_next_due_date = timezone.now()
        task_service_model.complete_task(task=repeatable_task_instance_without_due_date)

        assert repeatable_task_instance_without_due_date.status == task_model.status_active
        assert repeatable_task_instance_without_due_date.due_date.date() == expected_next_due_date.date()

    def test_complete_one_time_task_changes_status_to_completed(self, task_model, task_service_model, task_instance):
        task_service_model.complete_task(task=task_instance)

        assert task_instance.status == task_model.status_completed

    def test_mark_already_completed_one_time_task_as_completed_throws_error(self, task_service_model,
                                                                            completed_task_instance):
        with pytest.raises(TaskException):
            task_service_model.complete_task(completed_task_instance)

    def test_mark_task_as_completed_saves_pomodoro_in_progress_state(self, task_service_model, task_instance,
                                                                     task_event_in_progress):
        assert task_event_in_progress.start is not None and task_event_in_progress.end is None
        task_service_model.complete_task(task=task_instance, active_task_event=task_event_in_progress)

        assert task_event_in_progress.end is not None

    def test_bring_completed_one_time_task_to_active_tasks(self, task_model, task_service_model,
                                                           completed_task_instance):
        task_service_model.reactivate_task(task=completed_task_instance)

        assert completed_task_instance.status == task_model.status_active


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
                                                                              exclude_id=sub_task_instance.id)

        assert is_name_available is True

# class TestTaskEventService:
#     def test_submit_pomodoro_with_valid_data(self):
#         pass
#
#     def test_submit_pomodoro_with_start_date_greater_than_end(self):
#         pass
#
#     def test_submit_pomodoro_with_overlapping_time_frames(self):
#         pass
#
#     def test_submit_pomodoro_for_already_completed_task_results_with_error(self):
#         pass
#
#     def test_submit_pomodoro_with_invalid_pomodoro_duration_selected_by_user(self):
#         pass
