import pytest

from pomodorr.projects.services import ProjectDomainModel, PriorityDomainModel, TaskDomainModel

pytestmark = pytest.mark.django_db


class TestProjectServices:

    def test_get_active_projects_for_user(self, project_instance_removed, project_create_batch, active_user):
        service_method_result = ProjectDomainModel.get_active_projects_for_user(user=active_user)

        assert service_method_result.count() == 5
        assert project_instance_removed not in service_method_result
        assert all(project in service_method_result for project in project_create_batch)

    def test_get_removed_projects_for_user(self, active_user, project_instance_for_random_user, project_instance,
                                           removed_project_create_batch):
        service_method_result = ProjectDomainModel.get_removed_projects_for_user(user=active_user)

        assert service_method_result.count() == 5
        assert project_instance not in service_method_result
        assert project_instance_for_random_user not in service_method_result
        assert all(project in service_method_result for project in removed_project_create_batch)

    def test_get_all_projects_for_user(self, active_user, project_instance_for_random_user, project_create_batch):
        service_method_result = ProjectDomainModel.get_all_projects_for_user(user=active_user)

        assert service_method_result.count() == 5
        assert project_instance_for_random_user not in service_method_result
        assert all(project in service_method_result for project in project_create_batch)

    def test_get_all_active_projects(self, project_instance_removed, project_create_batch):
        service_method_result = ProjectDomainModel.get_all_active_projects()

        assert service_method_result.count() == 5
        assert project_instance_removed not in service_method_result
        assert all(project in service_method_result for project in project_create_batch)

    def test_get_all_removed_projects(self, project_instance, removed_project_create_batch):
        service_method_result = ProjectDomainModel.get_all_removed_projects()

        assert service_method_result.count() == 5
        assert project_instance not in service_method_result
        assert all(project in service_method_result for project in removed_project_create_batch)

    def test_get_all_projects(self, project_create_batch, project_instance_removed):
        service_method_result = ProjectDomainModel.get_all_projects()

        assert service_method_result.count() == 6
        assert project_instance_removed in service_method_result
        assert all(project in service_method_result for project in project_create_batch)

    def test_hard_delete_projects_on_queryset(self, project_create_batch, active_user):
        user_projects = ProjectDomainModel.get_all_projects_for_user(user=active_user)
        ProjectDomainModel.hard_delete_on_queryset(queryset=user_projects)

        assert user_projects.count() == 0

    def test_undo_delete_projects_on_queryset(self, removed_project_create_batch):
        all_removed_projects = ProjectDomainModel.get_all_removed_projects()
        assert all(project.is_removed is True for project in all_removed_projects)

        ProjectDomainModel.undo_delete_on_queryset(queryset=all_removed_projects)
        assert all(project.is_removed is True for project in all_removed_projects.all())


class TestPriorityServices:
    def test_get_all_priorities(self, priority_instance, priority_create_batch):
        service_method_results = PriorityDomainModel.get_all_priorities()

        assert service_method_results.count() == 6
        assert priority_instance in service_method_results
        assert all(priority in service_method_results for priority in priority_create_batch)

    def test_get_all_priorities_for_user(self, priority_instance_for_random_user, priority_create_batch, active_user):
        service_method_result = PriorityDomainModel.get_priorities_for_user(user=active_user)

        assert service_method_result.count() == 5
        assert all(priority in service_method_result for priority in priority_create_batch)
        assert priority_instance_for_random_user not in service_method_result


class TestTaskServices:
    def test_get_active_tasks(self, task_instance, task_instance_completed):
        service_method_result = TaskDomainModel.get_active_tasks()

        assert service_method_result.count() == 1
        assert task_instance in service_method_result
        assert task_instance_completed not in service_method_result

    def test_get_completed_tasks(self, task_instance, task_instance_completed):
        service_method_result = TaskDomainModel.get_completed_tasks()

        assert service_method_result.count() == 1
        assert task_instance not in service_method_result
        assert task_instance_completed in service_method_result

    def test_get_removed_tasks(self, task_instance, task_instance_removed):
        service_method_result = TaskDomainModel.get_removed_tasks()

        assert service_method_result.count() == 1
        assert task_instance not in service_method_result
        assert task_instance_removed in service_method_result

    def test_get_all_tasks(self, task_instance, task_instance_removed, task_instance_completed):
        service_method_result = TaskDomainModel.get_all_tasks()

        assert service_method_result.count() == 3
        assert all(
            task in service_method_result for task in (task_instance, task_instance_removed, task_instance_completed))

    def test_get_active_tasks_for_user(self, task_instance, task_instance_completed, active_user):
        service_method_result = TaskDomainModel.get_active_tasks_for_user(user=active_user)

        assert service_method_result.count() == 1
        assert task_instance in service_method_result
        assert task_instance_completed not in service_method_result

    def test_get_completed_tasks_for_user(self, task_instance, task_instance_completed, active_user):
        service_method_result = TaskDomainModel.get_completed_tasks_for_user(user=active_user)

        assert service_method_result.count() == 1
        assert task_instance not in service_method_result
        assert task_instance_completed in service_method_result

    def test_get_removed_tasks_for_user(self, task_instance, task_instance_removed, active_user):
        service_method_result = TaskDomainModel.get_removed_tasks_for_user(user=active_user)

        assert service_method_result.count() == 1
        assert task_instance not in service_method_result
        assert task_instance_removed in service_method_result

    def test_get_all_tasks_for_user(self, task_instance, task_instance_removed, task_instance_completed,
                                    task_instance_for_random_project, active_user):
        service_method_result = TaskDomainModel.get_all_tasks_for_user(user=active_user)

        assert service_method_result.count() == 3
        assert task_instance_for_random_project not in service_method_result
        assert all(
            task in service_method_result for task in (task_instance, task_instance_removed, task_instance_completed))
