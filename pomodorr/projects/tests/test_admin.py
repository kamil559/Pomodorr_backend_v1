import pytest

from pomodorr.projects.selectors.project_selector import (
    get_all_projects, get_all_active_projects, get_all_removed_projects
)

pytestmark = pytest.mark.django_db


def test_get_queryset_returns_all_projects(request_mock, project_admin_view, project_create_batch,
                                           project_instance_removed):
    all_projects = list(get_all_projects())

    admin_get_queryset_result = list(project_admin_view.get_queryset(request=request_mock))

    assert project_instance_removed in all_projects
    assert all_projects == admin_get_queryset_result


def test_hard_delete(request_mock, project_admin_view, project_create_batch):
    all_projects = get_all_projects()

    assert all_projects.count() == 5

    project_admin_view.hard_delete(request=request_mock, queryset=all_projects)

    assert all_projects.count() == 0


def test_undo_delete(project_model, request_mock, project_admin_view, project_create_batch):
    active_projects = get_all_active_projects()
    removed_projects = get_all_removed_projects()
    assert active_projects.count() == 5

    project_model.objects.all().delete()
    assert active_projects.all().count() == 0
    assert removed_projects.all().count() == 5

    project_admin_view.undo_delete(request=request_mock, queryset=removed_projects)
    assert active_projects.all().count() == 5
    assert removed_projects.all().count() == 0
