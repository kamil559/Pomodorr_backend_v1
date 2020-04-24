import operator
from datetime import timedelta
from functools import reduce
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.db import IntegrityError
from django.utils import timezone
from pytest_lazyfixture import lazy_fixture

from pomodorr.projects.exceptions import TaskException, TaskEventException
from pomodorr.tools.utils import get_time_delta

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

    def test_complete_repeatable_task_creates_new_one_for_next_due_date(self, task_model, task_service_model,
                                                                        task_selector, repeatable_task_instance):
        completed_task = task_service_model.complete_task(task=repeatable_task_instance)
        expected_next_due_date = repeatable_task_instance.due_date + repeatable_task_instance.repeat_duration
        assert completed_task.status == task_model.status_completed
        next_task = task_selector.get_active_tasks(project=completed_task.project, name=completed_task.name)[0]

        assert next_task.status == task_model.status_active
        assert next_task.due_date.date() == expected_next_due_date.date()

    def test_complete_repeatable_task_without_due_date_sets_today_for_next_task_event(
        self, task_model, task_service_model, task_selector, repeatable_task_instance_without_due_date):
        assert repeatable_task_instance_without_due_date.due_date is None
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
        with pytest.raises(TaskException):
            task_service_model.complete_task(completed_task_instance)

    def test_mark_task_as_completed_saves_pomodoro_in_progress_state(self, task_service_model, task_instance,
                                                                     task_event_in_progress):
        assert task_event_in_progress.start is not None and task_event_in_progress.end is None
        task_service_model.complete_task(task=task_instance)
        task_event_in_progress.refresh_from_db()

        assert task_event_in_progress.end is not None

    def test_reactivate_one_time_task(self, task_model, task_service_model, completed_task_instance):
        task_service_model.reactivate_task(task=completed_task_instance)

        completed_task_instance.refresh_from_db()

        assert completed_task_instance.status == task_model.status_active

    def test_reactivate_one_time_task_with_existing_active_duplicate(self, task_service_model, task_instance,
                                                                     completed_task_instance):
        task_instance.name = completed_task_instance.name
        task_instance.save()

        with pytest.raises(IntegrityError):
            task_service_model.reactivate_task(task=completed_task_instance)

    def test_reactivate_repeatable_task(self, task_model, task_service_model, completed_repeatable_task_instance):
        task_service_model.reactivate_task(task=completed_repeatable_task_instance)

        completed_repeatable_task_instance.refresh_from_db()

        assert completed_repeatable_task_instance.status == task_model.status_active

    def test_reactivate_repeatable_task_with_existing_active_duplicate(self, task_service_model, task_instance,
                                                                       completed_repeatable_task_instance):
        task_instance.name = completed_repeatable_task_instance.name
        task_instance.save()

        with pytest.raises(IntegrityError):
            task_service_model.reactivate_task(task=completed_repeatable_task_instance)


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


class TestTaskEventService:
    @patch('pomodorr.projects.services.timezone')
    def test_start_pomodoro_with_valid_start_datetime_within_task(self, mock_timezone, task_event_service_model,
                                                                  task_instance, task_event_instance):
        mock_timezone.now.return_value = get_time_delta({'minutes': 60})

        task_event = task_event_service_model.start_pomodoro(task=task_instance)

        assert task_event is not None
        assert task_event.start is not None and task_event.end is None

    @patch('pomodorr.projects.services.timezone')
    def test_check_datetime_available_considers_only_today(self, mock_timezone, task_event_service_model, task_instance,
                                                           task_event_create_batch, task_event_in_progress):
        mock_timezone.now.return_value = (get_time_delta({'days': 1}))
        task_event = task_event_service_model.start_pomodoro(task=task_instance)

        assert task_event is not None
        assert task_event.start is not None and task_event.end is None

    @pytest.mark.parametrize(
        'mock_timezone_return_value, expected_exception',
        [
            (get_time_delta({'minutes': 10}, ahead=True), TaskEventException),
            (get_time_delta({'minutes': 60}, ahead=False), TaskEventException)
        ]
    )
    @patch('pomodorr.projects.services.timezone')
    def test_start_pomodoro_with_overlapping_start_datetime_within_task(self, mock_timezone,
                                                                        mock_timezone_return_value,
                                                                        expected_exception,
                                                                        task_event_service_model, task_instance,
                                                                        task_event_create_batch,
                                                                        task_event_in_progress):
        mock_timezone.now.return_value = mock_timezone_return_value

        with pytest.raises(expected_exception) as exc:
            task_event_service_model.start_pomodoro(task=task_instance)

        assert exc.value.code == TaskEventException.overlapping_pomodoro

    @patch('pomodorr.projects.services.cache')
    def test_start_pomodoro_with_already_existing_current_pomodoro(self, mock_cache, task_event_service_model,
                                                                   task_instance, task_event_in_progress):
        mock_cache.get.return_value = uuid4()

        with pytest.raises(TaskEventException) as exc:
            task_event_service_model.start_pomodoro(task=task_instance)

        assert exc.value.code == TaskEventException.current_pomodoro_exists

    def test_start_pomodoro_for_already_completed_task(self, task_event_service_model, completed_task_instance):
        with pytest.raises(TaskException) as exc:
            task_event_service_model.start_pomodoro(task=completed_task_instance)
        assert exc.value.code == TaskException.already_completed

    def test_finish_task_event_with_valid_end_datetime_within_task(self, task_event_service_model, task_instance,
                                                                   task_event_in_progress):
        task_event_service_model.finish_pomodoro(task_event=task_event_in_progress)

        assert task_event_in_progress.start < task_event_in_progress.end
        assert task_event_in_progress.end is not None

    @pytest.mark.parametrize(
        'mock_timezone_return_value, expected_exception',
        [
            (get_time_delta({'minutes': 10}, ahead=True), TaskEventException),
            (get_time_delta({'minutes': 60}, ahead=False), TaskEventException)
        ]
    )
    @patch('pomodorr.projects.services.timezone')
    def test_finish_task_event_with_overlapping_end_datetime_within_task(self, mock_timezone,
                                                                         mock_timezone_return_value,
                                                                         expected_exception, task_event_service_model,
                                                                         task_instance, task_event_create_batch,
                                                                         task_event_in_progress):
        mock_timezone.now.return_value = mock_timezone_return_value

        with pytest.raises(expected_exception) as exc:
            task_event_service_model.finish_pomodoro(task_event=task_event_in_progress)

        assert exc.value.code == TaskEventException.overlapping_pomodoro

    @patch('pomodorr.projects.services.timezone')
    def test_finish_task_event_with_too_long_pomodoro_duration(self, mock_timezone, task_event_service_model,
                                                               task_event_in_progress):
        mock_timezone.now.return_value = get_time_delta({'minutes': 30})

        with pytest.raises(TaskEventException) as exc:
            task_event_service_model.finish_pomodoro(task_event=task_event_in_progress)

        assert exc.value.code == TaskEventException.invalid_pomodoro_length

    @patch('pomodorr.projects.services.timezone')
    def test_finish_pomodoro_with_gaps(self, mock_timezone, task_event_service_model, task_event_in_progress_with_gaps):
        gaps_duration = reduce(operator.add,
                               (gap.end - gap.start for gap in task_event_in_progress_with_gaps.gaps.all()))
        expected_duration = timedelta(minutes=25)

        mock_timezone.now.return_value = get_time_delta({'minutes': 25}) + gaps_duration

        task_event_service_model.finish_pomodoro(task_event=task_event_in_progress_with_gaps)

        assert task_event_in_progress_with_gaps.end is not None
        assert task_event_in_progress_with_gaps.duration == expected_duration

    def test_finish_pomodoro_for_already_completed_task(self, task_event_service_model, completed_task_instance,
                                                        task_event_in_progress):
        task_event_in_progress.task = completed_task_instance
        task_event_in_progress.save()

        with pytest.raises(TaskException) as exc:
            task_event_service_model.finish_pomodoro(task_event=task_event_in_progress)
        assert exc.value.code == TaskException.already_completed

    @pytest.mark.parametrize(
        'start_date, end_date, excluded_task_event, expected_exception',
        [
            (get_time_delta({'minutes': 10}, ahead=True), None, None, TaskEventException),
            (get_time_delta({'minutes': 10}, ahead=False), None, None, TaskEventException),
            (get_time_delta({'minutes': 10}, ahead=True), get_time_delta({'minutes': 10}, ahead=True),
             lazy_fixture('task_event_instance'), TaskEventException),
            (get_time_delta({'minutes': 10}, ahead=False), get_time_delta({'minutes': 10}, ahead=True),
             lazy_fixture('task_event_instance'), TaskEventException)
        ]
    )
    def test_check_start_datetime_available(self, start_date, end_date, excluded_task_event, expected_exception,
                                            task_event_service_model, task_instance, task_event_create_batch,
                                            task_event_instance):
        with pytest.raises(expected_exception) as exc:
            task_event_service_model.check_datetime_available(task=task_instance, start_date=start_date,
                                                              end_date=end_date,
                                                              excluded_task_event=excluded_task_event)

        assert exc.value.code == TaskEventException.overlapping_pomodoro

    def test_get_task_event_duration_with_valid_finish_datetime(self, task_event_service_model, task_event_in_progress):
        finish_date_within_error_margin = task_event_in_progress.start + timedelta(minutes=25, seconds=59)

        task_event_duration = task_event_service_model.get_task_event_duration(
            task_event=task_event_in_progress, finish_datetime=finish_date_within_error_margin)

        assert task_event_duration == timedelta(minutes=25)

    def test_get_task_event_duration_with_shorter_duration(self, task_event_service_model, task_event_in_progress):
        finish_date_within_error_margin = task_event_in_progress.start + timedelta(minutes=5)

        task_event_duration = task_event_service_model.get_task_event_duration(
            task_event=task_event_in_progress, finish_datetime=finish_date_within_error_margin)

        assert task_event_duration == timedelta(minutes=5)

    def test_normalize_pomodoro_duration_with_valid_duration(self, task_event_service_model, task_event_in_progress):
        task_event_duration = timedelta(minutes=25, seconds=59)
        expected_normalized_duration = timedelta(minutes=25)

        normalized_duration = task_event_service_model.normalize_pomodoro_duration(
            task_event_duration=task_event_duration,
            task_event=task_event_in_progress,
            error_margin={'minutes': 1})

        assert normalized_duration == expected_normalized_duration

    def test_normalize_pomodoro_duration_with_shorter_duration(self, task_event_service_model, task_event_in_progress):
        task_event_duration = timedelta(minutes=5, seconds=10, milliseconds=12)
        expected_normalized_duration = task_event_duration

        normalized_duration = task_event_service_model.normalize_pomodoro_duration(
            task_event_duration=task_event_duration,
            task_event=task_event_in_progress,
            error_margin={'minutes': 1})

        assert normalized_duration == expected_normalized_duration

    def test_normalize_pomodoro_duration_with_too_long_duration(self, task_event_service_model, task_event_in_progress):
        task_event_duration = timedelta(minutes=26, microseconds=1)

        with pytest.raises(TaskEventException) as exc:
            task_event_service_model.normalize_pomodoro_duration(
                task_event_duration=task_event_duration,
                task_event=task_event_in_progress,
                error_margin={'minutes': 1})

        assert exc.value.code == TaskEventException.invalid_pomodoro_length

    @pytest.mark.xfail
    def test_get_pomodoro_length(self, task_event_service_model, task_instance):
        pomodoro_length = task_event_service_model.get_pomodoro_length(task=task_instance)

        assert pomodoro_length == task_instance.pomodoro_length

    @patch('pomodorr.projects.services.cache')
    def test_check_current_task_event_is_connected(self, mock_cache, task_event_service_model, task_event_in_progress):
        connection_id = uuid4()
        mock_cache.get.return_value = connection_id

        with pytest.raises(TaskEventException) as exc:
            task_event_service_model.check_current_task_event_is_connected(task_event=task_event_in_progress)

        assert exc.value.code == TaskEventException.current_pomodoro_exists

    def test_remove_task_event(self, task_event_service_model, task_event_instance):
        task_event_service_model.remove_task_event(task_event=task_event_instance)

        assert task_event_instance.id is None

    def test_remove_gaps(self, task_event_service_model, task_event_instance_with_unfinished_gaps):
        assert task_event_instance_with_unfinished_gaps.gaps.count() == 2

        task_event_service_model.remove_gaps(task_event=task_event_instance_with_unfinished_gaps)

        assert task_event_instance_with_unfinished_gaps.gaps.count() == 0
