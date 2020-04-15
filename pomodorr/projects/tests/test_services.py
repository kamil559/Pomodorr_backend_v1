import pytest

from pomodorr.projects.services import ProjectDomainModel

pytestmark = pytest.mark.django_db


def test_get_active_projects_for_user(project_model, project_instance_removed, project_create_batch, active_user):
    service_method_result = ProjectDomainModel.get_active_projects_for_user(user=active_user)
    orm_query_result = project_model.objects.filter(user=active_user)

    assert list(service_method_result) == list(orm_query_result)
    assert service_method_result.count() == 5


def test_get_removed_projects_for_user(project_model, active_user, project_instance_for_random_user,
                                       removed_project_create_batch):
    service_method_result = ProjectDomainModel.get_removed_projects_for_user(user=active_user)
    orm_query_result = project_model.all_objects.filter(is_removed=True, user=active_user)

    assert list(service_method_result) == list(orm_query_result)
    assert service_method_result.count() == 5


def test_get_all_projects_for_user(project_model, active_user, project_instance_for_random_user, project_create_batch):
    service_method_result = ProjectDomainModel.get_all_projects_for_user(user=active_user)
    orm_query_result = project_model.all_objects.filter(user=active_user)

    assert list(service_method_result) == list(orm_query_result)
    assert service_method_result.count() == 5


def test_get_all_active_projects(project_model, project_instance_removed, project_create_batch):
    service_method_result = ProjectDomainModel.get_all_active_projects()
    orm_query_result = project_model.objects.all()

    assert list(service_method_result) == list(orm_query_result)
    assert service_method_result.count() == 5


def test_get_all_removed_projects(project_model, project_instance, removed_project_create_batch):
    service_method_result = ProjectDomainModel.get_all_removed_projects()
    orm_query_result = project_model.all_objects.filter(is_removed=True)

    assert list(service_method_result) == list(orm_query_result)
    assert service_method_result.count() == 5


def test_get_all_projects(project_model, project_create_batch, project_instance_removed):
    service_method_result = ProjectDomainModel.get_all_projects()
    orm_query_result = project_model.all_objects.all()

    assert list(service_method_result) == list(orm_query_result)
    assert service_method_result.count() == 6


def test_hard_delete_on_queryset(project_create_batch, active_user):
    user_projects = ProjectDomainModel.get_all_projects_for_user(user=active_user)
    ProjectDomainModel.hard_delete_on_queryset(queryset=user_projects)

    assert user_projects.count() == 0


def test_undo_delete_on_queryset(removed_project_create_batch):
    all_removed_projects = ProjectDomainModel.get_all_removed_projects()
    assert all(project.is_removed is True for project in all_removed_projects)

    ProjectDomainModel.undo_delete_on_queryset(queryset=all_removed_projects)
    assert all(project.is_removed is True for project in all_removed_projects.all())
