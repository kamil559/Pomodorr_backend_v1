import pytest

from pomodorr.projects.selectors import ProjectSelector, PrioritySelector, TaskSelector, SubTaskSelector, \
    TaskEventSelector

pytestmark = pytest.mark.django_db


class TestProjectSelector:
    def test_get_active_projects_for_user(self, project_instance_removed, project_create_batch, active_user):
        selector_method_result = ProjectSelector.get_active_projects_for_user(user=active_user)

        assert selector_method_result.count() == 5
        assert project_instance_removed not in selector_method_result
        assert all(project in selector_method_result for project in project_create_batch)

    def test_get_removed_projects_for_user(self, active_user, project_instance_for_random_user, project_instance,
                                           removed_project_create_batch):
        selector_method_result = ProjectSelector.get_removed_projects_for_user(user=active_user)

        assert selector_method_result.count() == 5
        assert project_instance not in selector_method_result
        assert project_instance_for_random_user not in selector_method_result
        assert all(project in selector_method_result for project in removed_project_create_batch)

    def test_get_all_projects_for_user(self, active_user, project_instance_for_random_user, project_create_batch):
        selector_method_result = ProjectSelector.get_all_projects_for_user(user=active_user)

        assert selector_method_result.count() == 5
        assert project_instance_for_random_user not in selector_method_result
        assert all(project in selector_method_result for project in project_create_batch)

    def test_get_all_active_projects(self, project_instance_removed, project_create_batch):
        selector_method_result = ProjectSelector.get_all_active_projects()

        assert selector_method_result.count() == 5
        assert project_instance_removed not in selector_method_result
        assert all(project in selector_method_result for project in project_create_batch)

    def test_get_all_removed_projects(self, project_instance, removed_project_create_batch):
        selector_method_result = ProjectSelector.get_all_removed_projects()

        assert selector_method_result.count() == 5
        assert project_instance not in selector_method_result
        assert all(project in selector_method_result for project in removed_project_create_batch)

    def test_get_all_projects(self, project_create_batch, project_instance_removed):
        selector_method_result = ProjectSelector.get_all_projects()

        assert selector_method_result.count() == 6
        assert project_instance_removed in selector_method_result
        assert all(project in selector_method_result for project in project_create_batch)

    def test_hard_delete_projects_on_queryset(self, project_create_batch, active_user):
        user_projects = ProjectSelector.get_all_projects_for_user(user=active_user)
        ProjectSelector.hard_delete_on_queryset(queryset=user_projects)

        assert user_projects.count() == 0

    def test_undo_delete_projects_on_queryset(self, removed_project_create_batch):
        all_removed_projects = ProjectSelector.get_all_removed_projects()
        assert all(project.is_removed is True for project in all_removed_projects)

        ProjectSelector.undo_delete_on_queryset(queryset=all_removed_projects)
        assert all(project.is_removed is True for project in all_removed_projects.all())


class TestPrioritySelector:
    def test_get_all_priorities(self, priority_instance, priority_create_batch):
        selector_method_results = PrioritySelector.get_all_priorities()

        assert selector_method_results.count() == 6
        assert priority_instance in selector_method_results
        assert all(priority in selector_method_results for priority in priority_create_batch)

    def test_get_all_priorities_for_user(self, priority_instance_for_random_user, priority_create_batch, active_user):
        selector_method_result = PrioritySelector.get_priorities_for_user(user=active_user)

        assert selector_method_result.count() == 5
        assert all(priority in selector_method_result for priority in priority_create_batch)
        assert priority_instance_for_random_user not in selector_method_result


class TestTaskSelector:
    def test_get_active_tasks(self, task_instance, task_instance_completed):
        selector_method_result = TaskSelector.get_active_tasks()

        assert selector_method_result.count() == 1
        assert task_instance in selector_method_result
        assert task_instance_completed not in selector_method_result

    def test_get_completed_tasks(self, task_instance, task_instance_completed):
        selector_method_result = TaskSelector.get_completed_tasks()

        assert selector_method_result.count() == 1
        assert task_instance not in selector_method_result
        assert task_instance_completed in selector_method_result

    def test_get_removed_tasks(self, task_instance, task_instance_removed):
        selector_method_result = TaskSelector.get_removed_tasks()

        assert selector_method_result.count() == 1
        assert task_instance not in selector_method_result
        assert task_instance_removed in selector_method_result

    def test_get_all_tasks(self, task_instance, task_instance_removed, task_instance_completed):
        selector_method_result = TaskSelector.get_all_tasks()

        assert selector_method_result.count() == 3
        assert all(
            task in selector_method_result for task in (task_instance, task_instance_removed, task_instance_completed))

    def test_get_active_tasks_for_user(self, task_instance, task_instance_completed, active_user):
        selector_method_result = TaskSelector.get_active_tasks_for_user(user=active_user)

        assert selector_method_result.count() == 1
        assert task_instance in selector_method_result
        assert task_instance_completed not in selector_method_result

    def test_get_completed_tasks_for_user(self, task_instance, task_instance_completed, active_user):
        selector_method_result = TaskSelector.get_completed_tasks_for_user(user=active_user)

        assert selector_method_result.count() == 1
        assert task_instance not in selector_method_result
        assert task_instance_completed in selector_method_result

    def test_get_removed_tasks_for_user(self, task_instance, task_instance_removed, active_user):
        selector_method_result = TaskSelector.get_removed_tasks_for_user(user=active_user)

        assert selector_method_result.count() == 1
        assert task_instance not in selector_method_result
        assert task_instance_removed in selector_method_result

    def test_get_all_tasks_for_user(self, task_instance, task_instance_removed, task_instance_completed,
                                    task_instance_for_random_project, active_user):
        selector_method_result = TaskSelector.get_all_tasks_for_user(user=active_user)

        assert selector_method_result.count() == 3
        assert task_instance_for_random_project not in selector_method_result
        assert all(
            task in selector_method_result for task in (task_instance, task_instance_removed, task_instance_completed))


class TestSubTaskSelector:
    def test_get_all_sub_tasks(self, sub_task_instance, sub_task_for_random_task):
        selector_method_result = SubTaskSelector.get_all_sub_tasks()

        assert selector_method_result.count() == 2
        assert all(
            sub_task in selector_method_result for sub_task in (sub_task_instance, sub_task_for_random_task))

    def test_get_get_all_sub_tasks_for_task(self, sub_task_instance, sub_task_for_random_task, task_instance):
        selector_method_result = SubTaskSelector.get_all_sub_tasks_for_task(task=task_instance)

        assert selector_method_result.count() == 1
        assert sub_task_instance in selector_method_result
        assert sub_task_for_random_task not in selector_method_result


class TestTaskEventSelector:
    def test_get_all_task_events(self, task_event_create_batch):
        selector_method_result = TaskEventSelector.get_all_task_events()

        assert selector_method_result.count() == 5
        assert all(task_event in selector_method_result for task_event in task_event_create_batch)

    def test_get_all_task_events_for_user(self, task_event_create_batch, task_event_for_random_task, active_user):
        selector_method_result = TaskEventSelector.get_all_task_events_for_user(user=active_user)

        assert selector_method_result.count() == 5
        assert task_event_for_random_task not in selector_method_result
        assert all(task_event in selector_method_result for task_event in task_event_create_batch)

    def test_get_all_task_events_for_project(self, task_event_create_batch, task_event_for_random_task,
                                             project_instance):
        selector_method_result = TaskEventSelector.get_all_task_events_for_project(project=project_instance)

        assert selector_method_result.count() == 5
        assert task_event_for_random_task not in selector_method_result
        assert all(task_event in selector_method_result for task_event in task_event_create_batch)

    def test_get_all_task_events_for_task(self, task_event_create_batch, task_event_for_random_task, task_instance):
        selector_method_result = TaskEventSelector.get_all_task_events_for_task(task=task_instance)

        assert selector_method_result.count() == 5
        assert task_event_for_random_task not in selector_method_result
        assert all(task_event in selector_method_result for task_event in task_event_create_batch)
