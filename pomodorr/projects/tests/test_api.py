import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import force_authenticate
from social_core.pipeline import user

from pomodorr.projects.api import ProjectsViewSet
from pomodorr.projects.services import ProjectDomainModel
from pomodorr.tools.utils import reverse_query_params

pytestmark = pytest.mark.django_db


def test_user_creates_new_project_with_valid_data(project_data, active_user, request_factory):
    url = reverse('api:project-list')
    view = ProjectsViewSet.as_view({'post': 'create'})
    request = request_factory.post(url, project_data)
    force_authenticate(request=request, user=active_user)

    response = view(request)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert all([key in response.data.keys() for key in project_data] and
               [value in response.data.values() for value in response.data.values()])


def test_user_tries_to_create_new_project_with_invalid_data(project_data, active_user, request_factory):
    project_data = project_data.fromkeys(project_data, '')
    url = reverse('api:project-list')
    view = ProjectsViewSet.as_view({'post': 'create'})
    request = request_factory.post(url, project_data)
    force_authenticate(request=request, user=active_user)

    response = view(request)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['name'][0] == 'This field may not be blank.'


def test_user_tries_to_create_new_project_without_authorization(project_data, request_factory):
    project_data = project_data.fromkeys(project_data, '')
    url = reverse('api:project-list')
    view = ProjectsViewSet.as_view({'post': 'create'})
    request = request_factory.post(url, project_data)

    response = view(request)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_user_gets_his_projects(project_create_batch, request_factory, active_user):
    url = reverse('api:project-list')
    view = ProjectsViewSet.as_view({'get': 'list'})
    request = request_factory.get(url)
    force_authenticate(request=request, user=active_user)

    response = view(request)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 5
    assert response.data['results'] is not None


def test_user_tries_to_get_his_projects_without_authorization(project_create_batch, request_factory):
    url = reverse('api:project-list')
    view = ProjectsViewSet.as_view({'get': 'list'})
    request = request_factory.get(url)

    response = view(request)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_user_gets_project_detail(project_instance, request_factory, active_user):
    url = reverse('api:project-detail', kwargs={'pk': project_instance.pk})
    view = ProjectsViewSet.as_view({'get': 'retrieve'})
    request = request_factory.get(url)
    force_authenticate(request=request, user=active_user)

    response = view(request, pk=project_instance.pk)

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None


def test_user_tries_to_get_project_detail_without_authorization(project_instance, request_factory):
    url = reverse('api:project-detail', kwargs={'pk': project_instance.pk})
    view = ProjectsViewSet.as_view({'get': 'retrieve'})
    request = request_factory.get(url)

    response = view(request, pk=project_instance.pk)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_user_tries_to_get_someone_elses_project_detail(active_user, project_instance_for_random_user, request_factory):
    url = reverse('api:project-detail', kwargs={'pk': project_instance_for_random_user.pk})
    view = ProjectsViewSet.as_view({'get': 'retrieve'})
    request = request_factory.get(url)
    force_authenticate(request=request, user=active_user)

    response = view(request, pk=project_instance_for_random_user.pk)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    'ordering',
    ['created_at', '-created_at', 'priority', '-priority', 'user_defined_ordering', '-user_defined_ordering'])
def test_user_gets_his_projects_ordered(ordering, project_create_batch, request_factory, active_user):
    url = reverse_query_params('api:project-list', query_kwargs={'ordering': ordering})
    view = ProjectsViewSet.as_view({'get': 'list'})
    request = request_factory.get(url)
    force_authenticate(request=request, user=active_user)

    response = view(request)

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert 'results' in response.data

    response_result_ids = [record['id'] for record in response.data['results']]
    sorted_orm_fetched_projects = list(map(
        lambda uuid: str(uuid),
        ProjectDomainModel.get_active_projects_for_user(user=active_user).order_by(ordering).values_list('id',
                                                                                                         flat=True)))
    assert response_result_ids == sorted_orm_fetched_projects


@pytest.mark.parametrize('ordering', ['id', '-id', 'xyz', '-xyz'])
def test_user_gets_his_projects_ordered_by_forbidden_fields(ordering, project_create_batch, request_factory,
                                                            active_user):
    #  Ordering by non-existing fields for model or by fields not specified in serializer ordering
    #  should return records ordered by default ordering specified in serializer or model

    url = reverse_query_params('api:project-list', query_kwargs={'ordering': ordering})
    view = ProjectsViewSet.as_view({'get': 'list'})
    request = request_factory.get(url)
    force_authenticate(request=request, user=active_user)
    response = view(request)

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert 'results' in response.data

    response_result_ids = [record['id'] for record in response.data['results']]
    default_sorted_orm_fetched_projects = list(map(
        lambda uuid: str(uuid),
        ProjectDomainModel.get_active_projects_for_user(user=active_user).values_list('id', flat=True)))
    assert response_result_ids == default_sorted_orm_fetched_projects


def test_user_updates_his_project_with_valid_data(project_data, project_instance, active_user, request_factory):
    project_data['id'] = project_instance.id
    url = reverse('api:project-detail', kwargs={'pk': project_instance.pk})
    view = ProjectsViewSet.as_view({'put': 'update'})
    request = request_factory.put(url, project_data)
    force_authenticate(request=request, user=active_user)

    response = view(request, pk=project_instance.pk)

    assert response.status_code == status.HTTP_200_OK
    assert all([key in response.data.keys() for key in project_data] and
               [value in response.data.values() for value in response.data.values()])


def test_user_updates_his_project_with_invalid_data(project_data, project_instance, active_user, request_factory):
    project_data = project_data.fromkeys(project_data, '')
    url = reverse('api:project-detail', kwargs={'pk': project_instance.pk})
    view = ProjectsViewSet.as_view({'put': 'update'})
    request = request_factory.put(url, project_data)
    force_authenticate(request=request, user=active_user)

    response = view(request, pk=project_instance.pk)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['name'][0] == 'This field may not be blank.'


def test_user_updates_his_project_without_authorization(project_data, project_instance, active_user, request_factory):
    project_data['id'] = project_instance.id
    url = reverse('api:project-detail', kwargs={'pk': project_instance.pk})
    view = ProjectsViewSet.as_view({'put': 'update'})

    request = request_factory.put(url, project_data)

    response = view(request, pk=project_instance.pk)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_user_tries_to_update_someone_elses_project(project_data, active_user, project_instance_for_random_user,
                                                    request_factory):
    project_data['id'] = project_instance_for_random_user.id
    url = reverse('api:project-detail', kwargs={'pk': project_instance_for_random_user.pk})
    view = ProjectsViewSet.as_view({'put': 'update'})
    request = request_factory.put(url, project_data)
    force_authenticate(request=request, user=active_user)

    response = view(request, pk=project_instance_for_random_user.pk)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_user_deletes_his_project(project_instance, active_user, request_factory):
    url = reverse('api:project-detail', kwargs={'pk': project_instance.pk})
    view = ProjectsViewSet.as_view({'delete': 'destroy'})
    request = request_factory.delete(url)
    force_authenticate(request=request, user=active_user)

    response = view(request, pk=project_instance.pk)

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_user_tries_to_delete_his_project_without_authorization(project_instance, request_factory):
    url = reverse('api:project-detail', kwargs={'pk': project_instance.pk})
    view = ProjectsViewSet.as_view({'delete': 'destroy'})
    request = request_factory.delete(url)

    response = view(request, pk=project_instance.pk)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_user_tries_to_delete_someone_elses_project(active_user, project_instance_for_random_user, request_factory):
    url = reverse('api:project-detail', kwargs={'pk': project_instance_for_random_user.pk})
    view = ProjectsViewSet.as_view({'delete': 'destroy'})
    request = request_factory.delete(url)
    force_authenticate(request=request, user=user)

    response = view(request, pk=project_instance_for_random_user.pk)

    assert response.status_code == status.HTTP_404_NOT_FOUND
