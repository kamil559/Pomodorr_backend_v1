import random
from datetime import timedelta

import factory
import pytest
from django.urls import reverse
from django.utils.http import urlencode
from pytest_lazyfixture import lazy_fixture
from rest_framework import status
from rest_framework.test import force_authenticate

from pomodorr.projects.api import ProjectsViewSet, PriorityViewSet, TaskViewSet
from pomodorr.projects.exceptions import PriorityException, TaskException
from pomodorr.projects.selectors import ProjectSelector, PrioritySelector, TaskSelector
from pomodorr.tools.utils import reverse_query_params, get_time_delta

pytestmark = pytest.mark.django_db


class TestPriorityViewSet:
    base_url = 'api/priorities/'
    detail_url = 'api/priorities/{pk}/'

    def test_create_priority_with_valid_data(self, priority_data, active_user, request_factory):
        view = PriorityViewSet.as_view({'post': 'create'})
        request = request_factory.post(self.base_url, priority_data)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data is not None
        assert all([key in response.data.keys() for key in priority_data] and
                   [value in response.data.values() for value in response.data.values()])

    @pytest.mark.parametrize(
        'invalid_field_key, invalid_field_value',
        [
            ('name', factory.Faker('pystr', max_chars=129).generate()),
            ('name', ''),
            ('priority_level', random.randint(-999, -1)),
            ('priority_level', ''),
            ('color', factory.Faker('pystr', max_chars=19).generate()),
        ]
    )
    def test_create_priority_with_invalid_data(self, invalid_field_key, invalid_field_value, priority_data,
                                               active_user, request_factory):
        priority_data[invalid_field_key] = invalid_field_value
        view = PriorityViewSet.as_view({'post': 'create'})
        request = request_factory.post(self.base_url, priority_data)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert invalid_field_key in response.data

    def test_create_priority_with_duplicated_name(self, priority_data, priority_instance, active_user, request_factory):
        priority_data['name'] = priority_instance.name
        view = PriorityViewSet.as_view({'post': 'create'})
        request = request_factory.post(self.base_url, priority_data)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['name'][0] == PriorityException.messages[PriorityException.priority_duplicated]

    def test_get_priority_list(self, priority_create_batch, priority_instance_for_random_user, active_user,
                               request_factory):
        view = PriorityViewSet.as_view({'get': 'list'})
        request = request_factory.get(self.base_url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None
        assert response.data['count'] == 5

    @pytest.mark.parametrize(
        'ordering',
        ['created_at', '-created_at', 'priority_level', '-priority_level', 'name', '-name'])
    def test_get_priority_list_ordered_by_valid_fields(self, ordering, priority_create_batch, active_user,
                                                       request_factory):
        view = PriorityViewSet.as_view({'get': 'list'})
        url = f'{self.base_url}?{urlencode(query={"ordering": ordering})}'
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None

        response_result_ids = [record['id'] for record in response.data['results']]
        sorted_orm_fetched_priorities = list(map(
            lambda uuid: str(uuid),
            PrioritySelector.get_priorities_for_user(user=active_user).order_by(ordering).values_list('id', flat=True)))
        assert response_result_ids == sorted_orm_fetched_priorities

    @pytest.mark.parametrize(
        'ordering',
        ['color', '-color', 'user__password', '-user__password', 'user__id', 'user__id'])
    def test_get_priority_list_ordered_by_invalid_fields(self, ordering, priority_create_batch, active_user,
                                                         request_factory):
        view = PriorityViewSet.as_view({'get': 'list'})
        url = f'{self.base_url}?{urlencode(query={"ordering": ordering})}'
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None

        response_result_ids = [record['id'] for record in response.data['results']]
        default_sorted_orm_fetched_priorities = list(map(
            lambda uuid: str(uuid),
            PrioritySelector.get_priorities_for_user(user=active_user).values_list('id', flat=True)))
        assert response_result_ids == default_sorted_orm_fetched_priorities

    def test_get_priority_detail(self, priority_instance, active_user, request_factory):
        url = self.detail_url.format(pk=priority_instance.pk)
        view = PriorityViewSet.as_view({'get': 'retrieve'})
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=priority_instance.pk)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(priority_instance.id)

    def test_get_someone_elses_priority_detail(self, priority_instance, priority_instance_for_random_user, active_user,
                                               request_factory):
        url = self.detail_url.format(pk=priority_instance_for_random_user.pk)
        view = PriorityViewSet.as_view({'get': 'retrieve'})
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=priority_instance_for_random_user.pk)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_priority_with_valid_data(self, priority_data, priority_instance, active_user, request_factory):
        url = self.detail_url.format(pk=priority_instance.pk)
        view = PriorityViewSet.as_view({'put': 'update'})
        request = request_factory.put(url, priority_data)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=priority_instance.pk)

        assert response.status_code == status.HTTP_200_OK
        assert all([key in response.data.keys() for key in priority_data] and
                   [value in response.data.values() for value in response.data.values()])

    @pytest.mark.parametrize(
        'invalid_field_key, invalid_field_value',
        [
            ('name', factory.Faker('pystr', max_chars=129).generate()),
            ('name', ''),
            ('priority_level', random.randint(-999, -1)),
            ('priority_level', ''),
            ('color', factory.Faker('pystr', max_chars=19).generate()),
        ]
    )
    def test_update_priority_with_invalid_data(self, invalid_field_key, invalid_field_value, priority_data,
                                               priority_instance, active_user, request_factory):
        priority_data[invalid_field_key] = invalid_field_value
        url = self.detail_url.format(pk=priority_instance.pk)
        view = PriorityViewSet.as_view({'put': 'update'})
        request = request_factory.put(url, priority_data)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=priority_instance.pk)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert invalid_field_key in response.data

    def test_update_priority_with_duplicated_name(self, priority_data, priority_instance, priority_create_batch,
                                                  active_user, request_factory):
        priority_data['name'] = priority_create_batch[0].name
        url = self.detail_url.format(pk=priority_instance.pk)
        view = PriorityViewSet.as_view({'put': 'update'})
        request = request_factory.put(url, priority_data)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=priority_instance.pk)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['name'][0] == PriorityException.messages[PriorityException.priority_duplicated]

    def test_update_someone_elses_priority(self, priority_data, priority_instance_for_random_user, active_user,
                                           request_factory):
        url = self.detail_url.format(pk=priority_instance_for_random_user.pk)
        view = PriorityViewSet.as_view({'put': 'update'})
        request = request_factory.put(url, priority_data)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=priority_instance_for_random_user.pk)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_priority(self, priority_instance, active_user, request_factory):
        url = self.detail_url.format(pk=priority_instance.pk)
        view = PriorityViewSet.as_view({'delete': 'destroy'})
        request = request_factory.delete(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=priority_instance.id)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_someone_elses_priority(self, priority_instance_for_random_user, active_user, request_factory):
        url = self.detail_url.format(pk=priority_instance_for_random_user.pk)
        view = PriorityViewSet.as_view({'delete': 'destroy'})
        request = request_factory.delete(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=priority_instance_for_random_user.id)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestProjectsViewSet:
    def test_create_project_with_valid_data(self, project_data, active_user, request_factory):
        url = reverse('api:project-list')
        view = ProjectsViewSet.as_view({'post': 'create'})
        request = request_factory.post(url, project_data)
        force_authenticate(request=request, user=active_user)

        response = view(request)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data is not None
        assert all([key in response.data.keys() for key in project_data] and
                   [value in response.data.values() for value in response.data.values()])

    @pytest.mark.parametrize(
        'invalid_field_key, invalid_field_value',
        [
            ('name', factory.Faker('pystr', max_chars=129).generate()),
            ('name', ''),
            ('priority', random.randint(-999, -1)),
            ('priority', lazy_fixture('random_priority_id')),
            ('user_defined_ordering', random.randint(-999, -1)),
            ('user_defined_ordering', '')
        ]
    )
    def test_create_project_with_invalid_data(self, invalid_field_key, invalid_field_value, project_data, active_user,
                                              request_factory):
        project_data[invalid_field_key] = invalid_field_value
        url = reverse('api:project-list')
        view = ProjectsViewSet.as_view({'post': 'create'})
        request = request_factory.post(url, project_data)
        force_authenticate(request=request, user=active_user)

        response = view(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert invalid_field_key in response.data

    def test_create_project_with_duplicated_name(self):
        pass

    def test_get_project_list(self, project_create_batch, request_factory, active_user):
        url = reverse('api:project-list')
        view = ProjectsViewSet.as_view({'get': 'list'})
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)

        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5
        assert response.data['results'] is not None

    @pytest.mark.parametrize(
        'ordering',
        ['created_at', '-created_at', 'priority', '-priority', 'user_defined_ordering', '-user_defined_ordering'])
    def test_get_project_list_ordered_by_valid_fields(self, ordering, project_create_batch, request_factory,
                                                      active_user):
        url = reverse_query_params('api:project-list', query_kwargs={'ordering': ordering})
        view = ProjectsViewSet.as_view({'get': 'list'})
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)

        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None

        response_result_ids = [record['id'] for record in response.data['results']]
        sorted_orm_fetched_projects = list(map(
            lambda uuid: str(uuid),
            ProjectSelector.get_active_projects_for_user(user=active_user).order_by(ordering).values_list('id',
                                                                                                          flat=True)))
        assert response_result_ids == sorted_orm_fetched_projects

    @pytest.mark.parametrize('ordering', ['id', '-id', 'xyz', '-xyz'])
    def test_get_project_list_ordered_by_invalid_fields(self, ordering, project_create_batch, request_factory,
                                                        active_user):
        #  Ordering by non-existing fields for model or by fields not specified in serializer ordering
        #  should return records ordered by default ordering specified in serializer or model

        url = reverse_query_params('api:project-list', query_kwargs={'ordering': ordering})
        view = ProjectsViewSet.as_view({'get': 'list'})
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None

        response_result_ids = [record['id'] for record in response.data['results']]
        default_sorted_orm_fetched_projects = list(map(
            lambda uuid: str(uuid),
            ProjectSelector.get_active_projects_for_user(user=active_user).values_list('id', flat=True)))
        assert response_result_ids == default_sorted_orm_fetched_projects

    def test_get_project_detail(self, project_instance, request_factory, active_user):
        url = reverse('api:project-detail', kwargs={'pk': project_instance.pk})
        view = ProjectsViewSet.as_view({'get': 'retrieve'})
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)

        response = view(request, pk=project_instance.pk)

        assert response.status_code == status.HTTP_200_OK
        assert response.data is not None

    def test_get_someone_elses_project_detail(self, active_user, project_instance_for_random_user, request_factory):
        url = reverse('api:project-detail', kwargs={'pk': project_instance_for_random_user.pk})
        view = ProjectsViewSet.as_view({'get': 'retrieve'})
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)

        response = view(request, pk=project_instance_for_random_user.pk)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_project_with_valid_data(self, project_data, project_instance, active_user, request_factory):
        project_data['id'] = project_instance.id
        url = reverse('api:project-detail', kwargs={'pk': project_instance.pk})
        view = ProjectsViewSet.as_view({'put': 'update'})
        request = request_factory.put(url, project_data)
        force_authenticate(request=request, user=active_user)

        response = view(request, pk=project_instance.pk)

        assert response.status_code == status.HTTP_200_OK
        assert all([key in response.data.keys() for key in project_data] and
                   [value in response.data.values() for value in response.data.values()])

    @pytest.mark.parametrize(
        'invalid_field_key, invalid_field_value',
        [
            ('name', factory.Faker('pystr', max_chars=129).generate()),
            ('name', ''),
            ('priority', random.randint(-999, -1)),
            ('priority', lazy_fixture('random_priority_id')),
            ('user_defined_ordering', random.randint(-999, -1)),
            ('user_defined_ordering', '')
        ]
    )
    def test_update_project_with_invalid_data(self, invalid_field_key, invalid_field_value, project_data,
                                              project_instance, active_user, request_factory):
        project_data[invalid_field_key] = invalid_field_value
        url = reverse('api:project-detail', kwargs={'pk': project_instance.pk})
        view = ProjectsViewSet.as_view({'put': 'update'})
        request = request_factory.put(url, project_data)
        force_authenticate(request=request, user=active_user)

        response = view(request, pk=project_instance.pk)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert invalid_field_key in response.data

    def test_update_someone_elses_project(self, project_data, active_user, project_instance_for_random_user,
                                          request_factory):
        project_data['id'] = project_instance_for_random_user.id
        url = reverse('api:project-detail', kwargs={'pk': project_instance_for_random_user.pk})
        view = ProjectsViewSet.as_view({'put': 'update'})
        request = request_factory.put(url, project_data)
        force_authenticate(request=request, user=active_user)

        response = view(request, pk=project_instance_for_random_user.pk)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_project(self, project_instance, active_user, request_factory):
        url = reverse('api:project-detail', kwargs={'pk': project_instance.pk})
        view = ProjectsViewSet.as_view({'delete': 'destroy'})
        request = request_factory.delete(url)
        force_authenticate(request=request, user=active_user)

        response = view(request, pk=project_instance.pk)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_someone_elses_project(self, active_user, project_instance_for_random_user, request_factory):
        url = reverse('api:project-detail', kwargs={'pk': project_instance_for_random_user.pk})
        view = ProjectsViewSet.as_view({'delete': 'destroy'})
        request = request_factory.delete(url)
        force_authenticate(request=request, user=active_user)

        response = view(request, pk=project_instance_for_random_user.pk)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestTaskViewSet:
    base_url = 'api/tasks/'
    detail_url = 'api/tasks/{pk}/'

    def test_create_task_with_valid_data(self, task_data, project_instance, active_user, request_factory):
        task_data['project'] = project_instance.id
        view = TaskViewSet.as_view({'post': 'create'})
        request = request_factory.post(self.base_url, task_data)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data is not None
        assert all(key in response.data.keys() for key in task_data)

    @pytest.mark.parametrize(
        'invalid_field_key, invalid_field_value, get_field',
        [
            ('name', factory.Faker('pystr', max_chars=129).generate(), None),
            ('name', lazy_fixture('repeatable_task_instance'), 'name'),
            ('name', '', None),
            ('user_defined_ordering', random.randint(-999, -1), None),
            ('user_defined_ordering', '', None),
            ('pomodoro_number', 'xyz', None),
            ('repeat_duration', timedelta(minutes=5), None),
            ('repeat_duration', timedelta(days=5, minutes=5), None),
            ('pomodoro_length', timedelta(minutes=4), None),
            ('due_date', get_time_delta({'days': 1}, ahead=False), None),
            ('due_date', get_time_delta({'days': 1}, ahead=False).strftime('%Y-%m-%d'), None),
            ('priority', lazy_fixture('priority_instance_for_random_user'), 'id'),
            ('project', lazy_fixture('project_instance_for_random_user'), 'id'),
            ('project', '', None),
            ('status', 3, None),
            ('status', 1, None)
        ]
    )
    def test_crate_task_with_invalid_data(self, invalid_field_key, invalid_field_value, get_field, task_data,
                                          project_instance, active_user, request_factory):
        task_data['project'] = project_instance.id
        task_data[invalid_field_key] = invalid_field_value
        view = TaskViewSet.as_view({'post': 'create'})
        request = request_factory.post(self.base_url, task_data)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert len(response.data) == 1 and invalid_field_key in response.data

    def test_create_task_with_duplicated_name(self, task_data, task_instance, project_instance, active_user,
                                              request_factory):
        task_data['project'] = project_instance.id
        task_data['name'] = task_instance.name

        view = TaskViewSet.as_view({'post': 'create'})
        request = request_factory.post(self.base_url, task_data)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['name'][0] == TaskException.messages[TaskException.task_duplicated]

    def test_get_task_list(self, task_instance_create_batch, task_instance_for_random_project, active_user,
                           request_factory):
        view = TaskViewSet.as_view({'get': 'list'})
        request = request_factory.get(self.base_url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None
        assert response.data['count'] == 5

    @pytest.mark.parametrize(
        'ordering',
        ['created_at', '-created_at', 'priority', '-priority', 'user_defined_ordering', '-user_defined_ordering',
         'name', '-name'])
    def test_get_task_list_ordered_by_valid_fields(self, ordering, task_instance_create_batch, active_user,
                                                   request_factory):
        view = TaskViewSet.as_view({'get': 'list'})
        url = f'{self.base_url}?{urlencode(query={"ordering": ordering})}'
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None

        response_result_ids = [record['id'] for record in response.data['results']]
        sorted_orm_fetched_tasks = list(map(
            lambda uuid: str(uuid),
            TaskSelector.get_all_non_removed_tasks_for_user(user=active_user).order_by(ordering).values_list('id',
                                                                                                             flat=True)))
        assert response_result_ids == sorted_orm_fetched_tasks

    @pytest.mark.parametrize(
        'ordering',
        ['project__user__password', 'project__user__id', 'id', 'status', 'note'])
    def test_get_task_list_ordered_by_invalid_fields(self, ordering, task_instance_create_batch, active_user,
                                                     request_factory):
        view = TaskViewSet.as_view({'get': 'list'})
        url = f'{self.base_url}?{urlencode(query={"ordering": ordering})}'
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None

        response_result_ids = [record['id'] for record in response.data['results']]
        default_sorted_orm_fetched_tasks = list(map(
            lambda uuid: str(uuid),
            TaskSelector.get_all_non_removed_tasks_for_user(user=active_user).values_list('id', flat=True)))
        assert response_result_ids == default_sorted_orm_fetched_tasks

    def test_get_task_detail(self, task_instance, active_user, request_factory):
        url = self.detail_url.format(pk=task_instance.pk)
        view = TaskViewSet.as_view({'get': 'retrieve'})
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=task_instance.pk)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(task_instance.id)

    def test_get_someone_elses_task_detail(self, task_instance_for_random_project, active_user, request_factory):
        url = self.detail_url.format(pk=task_instance_for_random_project.pk)
        view = TaskViewSet.as_view({'get': 'retrieve'})
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=task_instance_for_random_project.pk)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_task_with_valid_data(self, task_data, task_instance, project_instance, active_user,
                                         request_factory):
        task_data['project'] = project_instance.id
        url = self.detail_url.format(pk=task_instance.pk)
        view = TaskViewSet.as_view({'put': 'update'})
        request = request_factory.put(url, task_data)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=task_instance.pk)

        assert response.status_code == status.HTTP_200_OK
        assert response.data is not None
        assert all(key in response.data.keys() for key in task_data)

    @pytest.mark.parametrize(
        'invalid_field_key, invalid_field_value, get_field',
        [
            ('name', factory.Faker('pystr', max_chars=129).generate(), None),
            ('name', lazy_fixture('repeatable_task_instance'), 'name'),
            ('name', '', None),
            ('user_defined_ordering', random.randint(-999, -1), None),
            ('user_defined_ordering', '', None),
            ('pomodoro_number', 'xyz', None),
            ('repeat_duration', timedelta(minutes=5), None),
            ('repeat_duration', timedelta(days=5, minutes=5), None),
            ('pomodoro_length', timedelta(minutes=4), None),
            ('due_date', get_time_delta({'days': 1}, ahead=False), None),
            ('due_date', get_time_delta({'days': 1}, ahead=False).strftime('%Y-%m-%d'), None),
            ('priority', lazy_fixture('priority_instance_for_random_user'), 'id'),
            ('project', lazy_fixture('project_instance_for_random_user'), 'id'),
            ('project', '', None),
            ('status', 3, None),
        ]
    )
    def test_update_task_with_invalid_data(self, invalid_field_key, invalid_field_value, get_field, task_data,
                                           task_instance, project_instance, active_user, request_factory):
        task_data['project'] = project_instance.id
        task_data[invalid_field_key] = invalid_field_value

        url = self.detail_url.format(pk=task_instance.pk)
        view = TaskViewSet.as_view({'put': 'update'})
        request = request_factory.put(url, task_data)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=task_instance.pk)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert invalid_field_key in response.data

    def test_update_task_with_duplicated_name(self, task_data, task_instance, repeatable_task_instance,
                                              project_instance, active_user, request_factory):
        task_data['project'] = project_instance.id
        task_data['name'] = repeatable_task_instance.name
        url = self.detail_url.format(pk=task_instance.pk)
        view = TaskViewSet.as_view({'put': 'update'})
        request = request_factory.put(url, task_data)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=task_instance.pk)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['name'][0] == TaskException.messages[TaskException.task_duplicated]

    def test_update_someone_elses_task(self, task_data, task_instance_for_random_project, project_instance, active_user,
                                       request_factory):
        task_data['project'] = project_instance.id
        url = self.detail_url.format(pk=task_instance_for_random_project.pk)
        view = TaskViewSet.as_view({'put': 'update'})
        request = request_factory.put(url, task_data)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=task_instance_for_random_project.pk)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_task(self, task_instance, active_user, request_factory):
        url = self.detail_url.format(pk=task_instance.pk)
        view = TaskViewSet.as_view({'delete': 'destroy'})
        request = request_factory.delete(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=task_instance.pk)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_someone_elses_task(self, task_instance_for_random_project, active_user, request_factory):
        url = self.detail_url.format(pk=task_instance_for_random_project.pk)
        view = TaskViewSet.as_view({'delete': 'destroy'})
        request = request_factory.delete(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=task_instance_for_random_project.pk)

        assert response.status_code == status.HTTP_404_NOT_FOUND
