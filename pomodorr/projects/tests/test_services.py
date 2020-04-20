import pytest

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

    def test_pin_task_with_statistics_preserved_to_new_project_with_non_colliding_name(self,
                                                                                       task_service_model,
                                                                                       project_instance, task_instance,
                                                                                       task_event_create_batch,
                                                                                       task_instance_in_second_project):
        assert task_instance_in_second_project.project is not task_instance.project

        updated_task = task_service_model.pin_to_project(task=task_instance_in_second_project, project=project_instance,
                                                         preserve_statistics=True)

        assert updated_task.project is task_instance.project
        assert updated_task.events.exists() is False
        assert all(task_event.task is task_instance for task_event in task_event_create_batch)

    def test_pin_task_with_statistics_preserved_to_new_project_with_colliding_name(self, task_service_model,
                                                                                   project_instance, task_instance,
                                                                                   duplicate_task_instance_in_second_project):
        assert duplicate_task_instance_in_second_project.name == task_instance.name
        assert duplicate_task_instance_in_second_project.project is not task_instance.project

        with pytest.raises(TaskException):
            task_service_model.pin_to_project(task=duplicate_task_instance_in_second_project, project=project_instance,
                                              preserve_statistics=False)

    # def test_shallow_pin_task_to_new_project_with_non_colliding_name_for_new_project(self):
    #     pass
    #
    # def test_shallow_pin_task_to_new_project_with_colliding_name_for_new_project(self):
    #     pass
    #
    # def test_mark_repeatable_task_as_completed_results_with_due_date_incrementation(self):
    #     pass
    #
    # def test_mark_one_time_task_results_with_changing_status_to_completed(self):
    #     pass
    #
    # def test_mark_already_completed_one_time_task_as_completed_results_with_error(self):
    #     pass
    #
    # def test_mark_task_as_completed_results_with_deleting_all_pomodoros_in_progress(self):
    #     pass
    #
    # def test_bring_completed_one_time_task_to_active_tasks(self):
    #     pass

#
# class SubTaskService:
#     def test_create_sub_task_with_valid_data(self):
#         pass
#
#     def test_create_sub_task_with_invalid_data(self):
#         pass
#
#     def test_create_sub_task_with_already_existing_name(self):
#         pass
#
#     def test_update_sub_task_with_valid_data(self):
#         pass
#
#     def test_update_sub_task_with_invalid_data(self):
#         pass
#
#     def test_update_sub_task_with_already_existing_name(self):
#         pass
#
#     def test_mark_sub_task_as_completed(self):
#         pass
#
#     def test_mark_sub_task_as_in_progress(self):
#         pass
#
#     def test_delete_sub_task(self):
#         pass
#
#
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
