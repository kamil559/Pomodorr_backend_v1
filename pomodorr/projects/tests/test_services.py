import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from pomodorr.projects.exceptions import TaskException
from pomodorr.projects.selectors.task_selector import get_active_tasks
from pomodorr.projects.services.project_service import is_project_name_available
from pomodorr.projects.services.sub_task_service import is_sub_task_name_available
from pomodorr.projects.services.task_service import (
    is_task_name_available, pin_to_project, complete_task, reactivate_task
)

pytestmark = pytest.mark.django_db


class TestProjectService:
    def test_check_project_name_is_available(self, project_data, active_user):
        checked_name = project_data['name']
        is_name_available = is_project_name_available(user=active_user, name=checked_name)

        assert is_name_available is True

    def test_check_project_name_is_not_available(self, project_instance, active_user):
        checked_name = project_instance.name
        is_name_available = is_project_name_available(user=active_user, name=checked_name)

        assert is_name_available is False

    def test_test_check_project_name_is_available_with_exclude_id(self, project_instance,
                                                                  active_user):
        checked_name = project_instance.name
        is_name_available = is_project_name_available(user=active_user, name=checked_name,
                                                      excluded=project_instance)

        assert is_name_available is True


class TestTaskService:
    def test_check_task_name_is_available(self, task_data, project_instance):
        checked_name = task_data['name']
        is_name_available = is_task_name_available(project=project_instance, name=checked_name)

        assert is_name_available is True

    def test_check_task_name_is_not_available(self, task_instance, project_instance):
        checked_name = task_instance.name
        is_name_available = is_task_name_available(project=project_instance, name=checked_name)

        assert is_name_available is False

    def test_check_task_name_is_available_with_exclude_id(self, task_instance, project_instance):
        checked_name = task_instance.name
        is_name_available = is_task_name_available(project=project_instance, name=checked_name, excluded=task_instance)

        assert is_name_available is True

    def test_pin_task_to_new_project_with_unique_name_for_new_project(self, second_project_instance,
                                                                      task_instance, date_frame_create_batch):
        updated_task = pin_to_project(task=task_instance, project=second_project_instance)

        assert updated_task.project is second_project_instance

    def test_pin_task_to_new_project_with_colliding_name_for_new_project(self, task_instance,
                                                                         duplicate_task_instance_in_second_project):
        new_project = duplicate_task_instance_in_second_project.project

        with pytest.raises(ValidationError) as exc:
            pin_to_project(task=task_instance, project=new_project)

        assert exc.value.messages[0] == TaskException.messages[TaskException.task_duplicated]

    def test_complete_repeatable_task_creates_new_one_for_next_due_date(self, task_model, repeatable_task_instance):
        completed_task = complete_task(task=repeatable_task_instance)
        expected_next_due_date = repeatable_task_instance.due_date + repeatable_task_instance.repeat_duration
        assert completed_task.status == task_model.status_completed
        next_task = get_active_tasks(project=completed_task.project, name=completed_task.name)[0]

        assert next_task.status == task_model.status_active
        assert next_task.due_date.date() == expected_next_due_date.date()

    def test_complete_repeatable_task_without_due_date_sets_today_for_next_date_frame(
        self, task_model, repeatable_task_instance_without_due_date):
        completed_task = complete_task(task=repeatable_task_instance_without_due_date)

        assert repeatable_task_instance_without_due_date.status == task_model.status_completed

        next_task = get_active_tasks(project=completed_task.project, name=completed_task.name)[0]

        assert next_task.status == task_model.status_active
        assert next_task.due_date.date() == timezone.now().date()

    def test_complete_one_time_task_changes_status_to_completed(self, task_model, task_instance):
        complete_task(task=task_instance)

        assert task_instance.status == task_model.status_completed

    def test_mark_already_completed_one_time_task_as_completed_throws_error(self, completed_task_instance):
        with pytest.raises(ValidationError) as exc:
            complete_task(completed_task_instance)

        assert exc.value.messages[0] == TaskException.messages[TaskException.already_completed]

    def test_mark_task_as_completed_saves_pomodoro_in_progress_state(self, task_instance, date_frame_in_progress):
        assert date_frame_in_progress.start is not None and date_frame_in_progress.end is None
        complete_task(task=task_instance)
        date_frame_in_progress.refresh_from_db()

        assert date_frame_in_progress.end is not None

    def test_reactivate_one_time_task(self, task_model, completed_task_instance):
        reactivate_task(task=completed_task_instance)

        completed_task_instance.refresh_from_db()

        assert completed_task_instance.status == task_model.status_active

    def test_reactivate_one_time_task_with_existing_active_duplicate(self, task_instance, completed_task_instance):
        task_instance.name = completed_task_instance.name
        task_instance.save()

        with pytest.raises(ValidationError) as exc:
            reactivate_task(task=completed_task_instance)
        assert exc.value.messages[0] == TaskException.messages[TaskException.task_duplicated]

    def test_reactivate_repeatable_task(self, task_model, completed_repeatable_task_instance):
        reactivate_task(task=completed_repeatable_task_instance)

        completed_repeatable_task_instance.refresh_from_db()

        assert completed_repeatable_task_instance.status == task_model.status_active

    def test_reactivate_repeatable_task_with_existing_active_duplicate(self, task_instance,
                                                                       completed_repeatable_task_instance):
        task_instance.name = completed_repeatable_task_instance.name
        task_instance.save()

        with pytest.raises(ValidationError) as exc:
            reactivate_task(task=completed_repeatable_task_instance)
        assert exc.value.messages[0] == TaskException.messages[TaskException.task_duplicated]


class TestSubTaskService:
    def test_check_sub_task_name_is_available(self, sub_task_data, task_instance):
        checked_name = sub_task_data['name']
        is_name_available = is_sub_task_name_available(task=task_instance, name=checked_name)

        assert is_name_available is True

    def test_check_sub_task_name_is_not_available(self, task_instance, sub_task_instance):
        checked_name = sub_task_instance.name
        is_name_available = is_sub_task_name_available(task=task_instance, name=checked_name)

        assert is_name_available is False

    def test_check_sub_task_name_is_available_with_exclude_id(self, task_instance, sub_task_instance):
        checked_name = sub_task_instance.name
        is_name_available = is_sub_task_name_available(task=task_instance, name=checked_name,
                                                       excluded=sub_task_instance)

        assert is_name_available is True
