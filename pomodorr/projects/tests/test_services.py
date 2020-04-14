import pytest

from pomodorr.projects.services import ProjectDomainModel


@pytest.mark.django_db
def test_get_active_projects_for_user(project_model, project_instance, project_create_batch,
                                      project_instance_for_random_user, active_user):
    project_instance.delete()
    service_method_result = list(ProjectDomainModel.get_active_projects_for_user(user=active_user))
    orm_query_result = list(project_model.objects.filter(user=active_user))

    assert service_method_result == orm_query_result
    assert project_instance not in service_method_result
    assert project_instance_for_random_user not in service_method_result
