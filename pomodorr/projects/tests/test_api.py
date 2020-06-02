import random
from datetime import timedelta

import factory
import pytest
from django.utils.http import urlencode
from pytest_lazyfixture import lazy_fixture
from rest_framework import status
from rest_framework.test import force_authenticate

from pomodorr.projects.api import ProjectsViewSet, PriorityViewSet, TaskViewSet, SubTaskViewSet
from pomodorr.projects.exceptions import PriorityException, TaskException, ProjectException, SubTaskException
from pomodorr.projects.selectors.priority_selector import get_priorities_for_user
from pomodorr.projects.selectors.project_selector import get_active_projects_for_user
from pomodorr.projects.selectors.sub_task_selector import get_all_sub_tasks_for_user, get_all_sub_tasks_for_task
from pomodorr.projects.selectors.task_selector import get_all_non_removed_tasks_for_user
from pomodorr.tools.utils import get_time_delta

pytestmark = pytest.mark.django_db


class TestPriorityViewSet:
    view_class = PriorityViewSet
    base_url = 'api/priorities/'
    detail_url = 'api/priorities/{pk}/'

    def test_create_priority_with_valid_data(self, priority_data, active_user, request_factory):
        view = self.view_class.as_view({'post': 'create'})
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
        view = self.view_class.as_view({'post': 'create'})
        request = request_factory.post(self.base_url, priority_data)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert invalid_field_key in response.data

    def test_create_priority_with_duplicated_name(self, priority_data, priority_instance, active_user, request_factory):
        priority_data['name'] = priority_instance.name
        view = self.view_class.as_view({'post': 'create'})
        request = request_factory.post(self.base_url, priority_data)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['name'][0] == PriorityException.messages[PriorityException.priority_duplicated]

    def test_get_priority_list(self, priority_create_batch, priority_instance_for_random_user, active_user,
                               request_factory):
        view = self.view_class.as_view({'get': 'list'})
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
        view = self.view_class.as_view({'get': 'list'})
        url = f'{self.base_url}?{urlencode(query={"ordering": ordering})}'
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None

        response_result_ids = [record['id'] for record in response.data['results']]
        sorted_orm_fetched_priorities = list(map(
            lambda uuid: str(uuid),
            get_priorities_for_user(user=active_user).order_by(ordering).values_list('id', flat=True)))
        assert response_result_ids == sorted_orm_fetched_priorities

    @pytest.mark.parametrize(
        'filter_lookup',
        [
            {'priority_level': 2},
            {'priority_level__gt': 2},
            {'priority_level__gte': 2},
            {'priority_level__lt': 2},
            {'priority_level__lte': 2},
            {'name': '0 Priority level 0'},
            {'name__iexact': '0 PRIORITY LEVEL 0'},
            {'name__contains': '0 PRIO'},
            {'name__icontains': '0 PRIO'}
        ]
    )
    def test_get_filtered_priority_list(self, filter_lookup, priority_create_batch, active_user, request_factory):
        view = self.view_class.as_view({'get': 'list'})
        url = f'{self.base_url}?{urlencode(query=filter_lookup)}'
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None

        response_result_ids = [record['id'] for record in response.data['results']]
        default_filtered_orm_fetched_priorities = list(map(
            lambda uuid: str(uuid),
            get_priorities_for_user(user=active_user).filter(**filter_lookup).values_list('id', flat=True)))
        assert response_result_ids == default_filtered_orm_fetched_priorities

    @pytest.mark.parametrize(
        'ordering',
        ['color', '-color', 'user__password', '-user__password', 'user__id', 'user__id'])
    def test_get_priority_list_ordered_by_invalid_fields(self, ordering, priority_create_batch, active_user,
                                                         request_factory):
        view = self.view_class.as_view({'get': 'list'})
        url = f'{self.base_url}?{urlencode(query={"ordering": ordering})}'
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None

        response_result_ids = [record['id'] for record in response.data['results']]
        default_sorted_orm_fetched_priorities = list(map(
            lambda uuid: str(uuid), get_priorities_for_user(user=active_user).values_list('id', flat=True)))
        assert response_result_ids == default_sorted_orm_fetched_priorities

    def test_get_priority_detail(self, priority_instance, active_user, request_factory):
        url = self.detail_url.format(pk=priority_instance.pk)
        view = self.view_class.as_view({'get': 'retrieve'})
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=priority_instance.pk)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(priority_instance.id)

    def test_get_someone_elses_priority_detail(self, priority_instance, priority_instance_for_random_user, active_user,
                                               request_factory):
        url = self.detail_url.format(pk=priority_instance_for_random_user.pk)
        view = self.view_class.as_view({'get': 'retrieve'})
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=priority_instance_for_random_user.pk)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_priority_with_valid_data(self, priority_data, priority_instance, active_user, request_factory):
        url = self.detail_url.format(pk=priority_instance.pk)
        view = self.view_class.as_view({'put': 'update'})
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
        view = self.view_class.as_view({'put': 'update'})
        request = request_factory.put(url, priority_data)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=priority_instance.pk)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert invalid_field_key in response.data

    def test_update_priority_with_duplicated_name(self, priority_data, priority_instance, priority_create_batch,
                                                  active_user, request_factory):
        priority_data['name'] = priority_create_batch[0].name
        url = self.detail_url.format(pk=priority_instance.pk)
        view = self.view_class.as_view({'put': 'update'})
        request = request_factory.put(url, priority_data)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=priority_instance.pk)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['name'][0] == PriorityException.messages[PriorityException.priority_duplicated]

    def test_update_someone_elses_priority(self, priority_data, priority_instance_for_random_user, active_user,
                                           request_factory):
        url = self.detail_url.format(pk=priority_instance_for_random_user.pk)
        view = self.view_class.as_view({'put': 'update'})
        request = request_factory.put(url, priority_data)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=priority_instance_for_random_user.pk)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_priority(self, priority_instance, active_user, request_factory):
        url = self.detail_url.format(pk=priority_instance.pk)
        view = self.view_class.as_view({'delete': 'destroy'})
        request = request_factory.delete(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=priority_instance.id)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_someone_elses_priority(self, priority_instance_for_random_user, active_user, request_factory):
        url = self.detail_url.format(pk=priority_instance_for_random_user.pk)
        view = self.view_class.as_view({'delete': 'destroy'})
        request = request_factory.delete(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=priority_instance_for_random_user.id)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestProjectsViewSet:
    view_class = ProjectsViewSet
    base_url = 'api/projects/'
    detail_url = 'api/projects/{pk}/'

    def test_create_project_with_valid_data(self, project_data, active_user, request_factory):
        url = self.base_url
        view = self.view_class.as_view({'post': 'create'})
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
        url = self.base_url
        view = self.view_class.as_view({'post': 'create'})
        request = request_factory.post(url, project_data)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert invalid_field_key in response.data

    def test_create_project_with_duplicated_name(self, project_data, project_instance, active_user, request_factory):
        project_data['name'] = project_instance.name
        url = self.base_url
        view = self.view_class.as_view({'post': 'create'})
        request = request_factory.post(url, project_data)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['name'][0] == ProjectException.messages[ProjectException.project_duplicated]

    def test_get_project_list(self, project_create_batch, request_factory, active_user):
        url = self.base_url
        view = self.view_class.as_view({'get': 'list'})
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5
        assert response.data['results'] is not None

    @pytest.mark.parametrize(
        'filter_lookup',
        [
            {'priority__priority_level': 2},
            {'priority__priority_level__gt': 2},
            {'priority__priority_level__gte': 2},
            {'priority__priority_level__lt': 2},
            {'priority__priority_level__lte': 2},
            {'name': '0 Project level 0'},
            {'name__iexact': 'Project 0'},
            {'name__contains': 'proj'},
            {'name__icontains': 'PROJ'}
        ]
    )
    def test_get_filtered_project_list(self, filter_lookup, project_create_batch, active_user, request_factory):
        view = self.view_class.as_view({'get': 'list'})
        url = f'{self.base_url}?{urlencode(query=filter_lookup)}'
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None

        response_result_ids = [record['id'] for record in response.data['results']]
        default_filtered_orm_fetched_projects = list(map(
            lambda uuid: str(uuid),
            get_active_projects_for_user(user=active_user).filter(**filter_lookup).values_list('id', flat=True)))
        assert response_result_ids == default_filtered_orm_fetched_projects

    @pytest.mark.parametrize(
        'ordering',
        ['created_at', '-created_at', 'priority', '-priority', 'user_defined_ordering', '-user_defined_ordering'])
    def test_get_project_list_ordered_by_valid_fields(self, ordering, project_create_batch, request_factory,
                                                      active_user):
        url = f'{self.base_url}?{urlencode(query={"ordering": ordering})}'
        view = self.view_class.as_view({'get': 'list'})
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None

        response_result_ids = [record['id'] for record in response.data['results']]
        sorted_orm_fetched_projects = list(map(
            lambda uuid: str(uuid),
            get_active_projects_for_user(user=active_user).order_by(ordering).values_list('id', flat=True)))
        assert response_result_ids == sorted_orm_fetched_projects

    @pytest.mark.parametrize('ordering', ['id', '-id', 'xyz', '-xyz'])
    def test_get_project_list_ordered_by_invalid_fields(self, ordering, project_create_batch, request_factory,
                                                        active_user):
        #  Ordering by non-existing fields for model or by fields not specified in serializer ordering
        #  should return records ordered by default ordering specified in serializer or model

        url = f'{self.base_url}?{urlencode(query={"ordering": ordering})}'
        view = self.view_class.as_view({'get': 'list'})
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None

        response_result_ids = [record['id'] for record in response.data['results']]
        default_sorted_orm_fetched_projects = list(map(
            lambda uuid: str(uuid), get_active_projects_for_user(user=active_user).values_list('id', flat=True)))
        assert response_result_ids == default_sorted_orm_fetched_projects

    def test_get_project_detail(self, project_instance, request_factory, active_user):
        url = self.detail_url.format(pk=project_instance.pk)
        view = self.view_class.as_view({'get': 'retrieve'})
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=project_instance.pk)

        assert response.status_code == status.HTTP_200_OK
        assert response.data is not None

    def test_get_someone_elses_project_detail(self, active_user, project_instance_for_random_user, request_factory):
        url = self.detail_url.format(pk=project_instance_for_random_user.pk)
        view = self.view_class.as_view({'get': 'retrieve'})
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=project_instance_for_random_user.pk)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_project_with_valid_data(self, project_data, project_instance, active_user, request_factory):
        project_data['id'] = project_instance.id
        url = self.detail_url.format(pk=project_instance.pk)
        view = self.view_class.as_view({'put': 'update'})
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
        url = self.detail_url.format(pk=project_instance.pk)
        view = self.view_class.as_view({'put': 'update'})
        request = request_factory.put(url, project_data)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=project_instance.pk)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert invalid_field_key in response.data

    def test_update_project_with_duplicated_name(self, project_data, project_instance, project_create_batch,
                                                 active_user, request_factory):
        project_data['name'] = project_create_batch[0].name
        project_data['id'] = project_instance.id
        url = self.detail_url.format(pk=project_instance.pk)
        view = self.view_class.as_view({'put': 'update'})
        request = request_factory.put(url, project_data)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=project_instance.pk)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['name'][0] == ProjectException.messages[ProjectException.project_duplicated]

    def test_update_someone_elses_project(self, project_data, active_user, project_instance_for_random_user,
                                          request_factory):
        project_data['id'] = project_instance_for_random_user.id
        url = self.detail_url.format(pk=project_instance_for_random_user.pk)
        view = self.view_class.as_view({'put': 'update'})
        request = request_factory.put(url, project_data)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=project_instance_for_random_user.pk)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_project(self, project_instance, active_user, request_factory):
        url = self.detail_url.format(pk=project_instance.pk)
        view = self.view_class.as_view({'delete': 'destroy'})
        request = request_factory.delete(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=project_instance.pk)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_someone_elses_project(self, active_user, project_instance_for_random_user, request_factory):
        url = self.detail_url.format(pk=project_instance_for_random_user.pk)
        view = self.view_class.as_view({'delete': 'destroy'})
        request = request_factory.delete(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=project_instance_for_random_user.pk)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestTaskViewSet:
    view_class = TaskViewSet
    base_url = 'api/tasks/'
    detail_url = 'api/tasks/{pk}/'

    def test_create_task_with_valid_data(self, task_data, project_instance, active_user, request_factory):
        task_data['project'] = project_instance.id
        view = self.view_class.as_view({'post': 'create'})
        request = request_factory.post(self.base_url, task_data)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data is not None

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
        view = self.view_class.as_view({'post': 'create'})
        request = request_factory.post(self.base_url, task_data)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert len(response.data) == 1 and invalid_field_key in response.data

    def test_create_task_with_duplicated_name(self, task_data, task_instance, project_instance, active_user,
                                              request_factory):
        task_data['project'] = project_instance.id
        task_data['name'] = task_instance.name

        view = self.view_class.as_view({'post': 'create'})
        request = request_factory.post(self.base_url, task_data)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['name'][0] == TaskException.messages[TaskException.task_duplicated]

    def test_get_task_list(self, task_instance_create_batch, task_instance_for_random_project, active_user,
                           request_factory):
        view = self.view_class.as_view({'get': 'list'})
        request = request_factory.get(self.base_url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None
        assert response.data['count'] == 5

    @pytest.mark.parametrize(
        'filter_lookup',
        [
            {'priority__priority_level': 2},
            {'priority__priority_level__gt': 2},
            {'priority__priority_level__gte': 2},
            {'priority__priority_level__lt': 2},
            {'priority__priority_level__lte': 2},
            {'name': '0 Project level 0'},
            {'name__iexact': 'Project 0'},
            {'name__contains': 'proj'},
            {'name__icontains': 'PROJ'}
        ]
    )
    def test_get_filtered_task_list(self, filter_lookup, task_instance_create_batch, active_user, request_factory):
        view = self.view_class.as_view({'get': 'list'})
        url = f'{self.base_url}?{urlencode(query=filter_lookup)}'
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None

        response_result_ids = [record['id'] for record in response.data['results']]
        default_filtered_orm_fetched_tasks = list(
            map(lambda uuid: str(uuid), get_all_non_removed_tasks_for_user(
                user=active_user).filter(**filter_lookup).values_list('id', flat=True)))
        assert response_result_ids == default_filtered_orm_fetched_tasks

    def test_get_task_list_for_project(self, project_instance, task_instance_create_batch,
                                       task_instance_in_second_project, active_user, request_factory):
        query_lookup = {'project__id': project_instance.id}
        view = self.view_class.as_view({'get': 'list'})
        url = f'{self.base_url}?{urlencode(query=query_lookup)}'
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None
        response_result_ids = [record['id'] for record in response.data['results']]
        assert str(task_instance_in_second_project.id) not in response_result_ids
        assert all(str(task.id) in response_result_ids for task in task_instance_create_batch)

    def test_get_task_list_for_someone_elses_project(self, task_instance_for_random_project,
                                                     task_instance_in_second_project, active_user, request_factory):
        query_lookup = {'project__id': task_instance_for_random_project.project.id}
        view = self.view_class.as_view({'get': 'list'})
        url = f'{self.base_url}?{urlencode(query=query_lookup)}'
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == []

    @pytest.mark.parametrize(
        'ordering',
        ['created_at', '-created_at', 'priority', '-priority', 'user_defined_ordering', '-user_defined_ordering',
         'name', '-name'])
    def test_get_task_list_ordered_by_valid_fields(self, ordering, task_instance_create_batch, active_user,
                                                   request_factory):
        view = self.view_class.as_view({'get': 'list'})
        url = f'{self.base_url}?{urlencode(query={"ordering": ordering})}'
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None

        response_result_ids = [record['id'] for record in response.data['results']]
        sorted_orm_fetched_tasks = list(map(
            lambda uuid: str(uuid),
            get_all_non_removed_tasks_for_user(user=active_user).order_by(ordering).values_list('id', flat=True)))
        assert response_result_ids == sorted_orm_fetched_tasks

    @pytest.mark.parametrize(
        'ordering',
        ['project__user__password', 'project__user__id', 'id', 'status', 'note'])
    def test_get_task_list_ordered_by_invalid_fields(self, ordering, task_instance_create_batch, active_user,
                                                     request_factory):
        view = self.view_class.as_view({'get': 'list'})
        url = f'{self.base_url}?{urlencode(query={"ordering": ordering})}'
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None

        response_result_ids = [record['id'] for record in response.data['results']]
        default_sorted_orm_fetched_tasks = list(map(
            lambda uuid: str(uuid), get_all_non_removed_tasks_for_user(user=active_user).values_list('id', flat=True)))
        assert response_result_ids == default_sorted_orm_fetched_tasks

    def test_get_task_detail(self, task_instance, active_user, request_factory):
        url = self.detail_url.format(pk=task_instance.pk)
        view = self.view_class.as_view({'get': 'retrieve'})
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=task_instance.pk)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(task_instance.id)

    def test_get_someone_elses_task_detail(self, task_instance_for_random_project, active_user, request_factory):
        url = self.detail_url.format(pk=task_instance_for_random_project.pk)
        view = self.view_class.as_view({'get': 'retrieve'})
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=task_instance_for_random_project.pk)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_task_with_valid_data(self, task_data, task_instance, project_instance, active_user,
                                         request_factory):
        task_data['project'] = project_instance.id
        url = self.detail_url.format(pk=task_instance.pk)
        view = self.view_class.as_view({'put': 'update'})
        request = request_factory.put(url, task_data)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=task_instance.pk)

        task_instance.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert response.data is not None
        task_data.pop('project')
        assert all([getattr(task_instance, key) == task_data[key] for key in task_data.keys()])

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
        view = self.view_class.as_view({'put': 'update'})
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
        view = self.view_class.as_view({'put': 'update'})
        request = request_factory.put(url, task_data)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=task_instance.pk)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['name'][0] == TaskException.messages[TaskException.task_duplicated]

    def test_update_someone_elses_task(self, task_data, task_instance_for_random_project, project_instance, active_user,
                                       request_factory):
        task_data['project'] = project_instance.id
        url = self.detail_url.format(pk=task_instance_for_random_project.pk)
        view = self.view_class.as_view({'put': 'update'})
        request = request_factory.put(url, task_data)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=task_instance_for_random_project.pk)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_task(self, task_instance, active_user, request_factory):
        url = self.detail_url.format(pk=task_instance.pk)
        view = self.view_class.as_view({'delete': 'destroy'})
        request = request_factory.delete(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=task_instance.pk)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_someone_elses_task(self, task_instance_for_random_project, active_user, request_factory):
        url = self.detail_url.format(pk=task_instance_for_random_project.pk)
        view = self.view_class.as_view({'delete': 'destroy'})
        request = request_factory.delete(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, pk=task_instance_for_random_project.pk)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestSubTaskViewSet:
    view_class = SubTaskViewSet
    base_url = 'api/tasks/{task_pk}/sub_tasks/'
    detail_url = 'api/tasks/{task_pk}/sub_tasks/{pk}/'

    def test_create_sub_task_with_valid_data(self, sub_task_data, task_instance, active_user, request_factory):
        sub_task_data['task'] = task_instance.id
        url = self.base_url.format(task_pk=task_instance.pk)
        view = self.view_class.as_view({'post': 'create'})
        request = request_factory.post(url, sub_task_data)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data is not None
        assert all([key in response.data.keys() for key in sub_task_data.keys()] and
                   [value in response.data.values() for value in sub_task_data.values()])

    @pytest.mark.parametrize(
        'invalid_field_key, invalid_field_value, get_field',
        [
            ('name', factory.Faker('pystr', max_chars=129).generate(), None),
            ('name', '', None),
            ('task', lazy_fixture('task_instance_for_random_project'), 'id'),
            ('task', '', None),
            ('is_completed', 123, None),
            ('is_completed', 'xyz', None),
        ]
    )
    def test_create_sub_task_with_invalid_data(self, invalid_field_key, invalid_field_value, get_field, sub_task_data,
                                               task_instance, active_user, request_factory):
        sub_task_data['task'] = task_instance.id
        if get_field is not None:
            sub_task_data[invalid_field_key] = getattr(invalid_field_value, get_field)
        else:
            sub_task_data[invalid_field_key] = invalid_field_value
        url = self.base_url.format(task_pk=task_instance.pk)
        view = self.view_class.as_view({'post': 'create'})
        request = request_factory.post(url, sub_task_data)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert invalid_field_key in response.data

    def test_create_sub_task_with_duplicated_name(self, sub_task_data, sub_task_instance, task_instance, active_user,
                                                  request_factory):
        sub_task_data['task'] = task_instance.id
        sub_task_data['name'] = sub_task_instance.name
        url = self.base_url.format(task_pk=task_instance.pk)
        view = self.view_class.as_view({'post': 'create'})
        request = request_factory.post(url, sub_task_data)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['name'][0] == SubTaskException.messages[SubTaskException.sub_task_duplicated]

    def test_get_sub_task_list(self, sub_task_create_batch, task_instance, active_user, request_factory):
        url = self.base_url.format(task_pk=task_instance.pk)
        view = self.view_class.as_view({'get': 'list'})
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, task_pk=task_instance.pk)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None
        assert response.data['count'] == 5

    @pytest.mark.parametrize(
        'filter_lookup',
        [
            {'name': '0 Project level 0'},
            {'name__iexact': 'Project 0'},
            {'name__contains': 'proj'},
            {'name__icontains': 'PROJ'},
            {'is_completed': True},
            {'is_completed': 1},
            {'is_completed': False},
            {'is_completed': 0},
        ]
    )
    def test_get_filtered_sub_task_list(self, filter_lookup, sub_task_create_batch, active_user, request_factory):
        view = self.view_class.as_view({'get': 'list'})
        url = f'{self.base_url}?{urlencode(query=filter_lookup)}'
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None

        response_result_ids = [record['id'] for record in response.data['results']]
        default_filtered_orm_fetched_sub_tasks = list(
            map(lambda uuid: str(uuid),
                get_all_sub_tasks_for_user(user=active_user).filter(**filter_lookup).values_list('id', flat=True)))
        assert response_result_ids == default_filtered_orm_fetched_sub_tasks

    def test_get_sub_task_list_for_task(self, task_instance, sub_task_create_batch, sub_task_for_random_task,
                                        active_user, request_factory):
        query_lookup = {'task__id': task_instance.id}
        view = self.view_class.as_view({'get': 'list'})
        url = f'{self.base_url}?{urlencode(query=query_lookup)}'
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None
        response_result_ids = [record['id'] for record in response.data['results']]
        assert str(sub_task_for_random_task.id) not in response_result_ids
        assert all(str(sub_task.id) in response_result_ids for sub_task in sub_task_create_batch)

    def test_get_sub_task_list_for_someone_elses_task(self, sub_task_for_random_task, active_user, request_factory):
        query_lookup = {'task__id': sub_task_for_random_task.task.id}
        view = self.view_class.as_view({'get': 'list'})
        url = f'{self.base_url}?{urlencode(query=query_lookup)}'
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == []

    @pytest.mark.parametrize(
        'ordering',
        ['created_at', '-created_at', 'name', '-name', 'is_completed', '-is_completed'])
    def test_get_sub_task_list_ordered_by_valid_fields(self, ordering, task_instance, sub_task_create_batch,
                                                       active_user, request_factory):
        view = self.view_class.as_view({'get': 'list'})
        base_url = self.base_url.format(task_pk=task_instance.pk)
        url = f'{base_url}?{urlencode(query={"ordering": ordering})}'
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, task_pk=task_instance.pk)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None

        response_result_ids = [record['id'] for record in response.data['results']]
        sorted_orm_fetched_sub_tasks = list(map(
            lambda uuid: str(uuid),
            get_all_sub_tasks_for_task(task=task_instance, task__project__user=active_user).order_by(
                ordering).values_list('id', flat=True)))
        assert response_result_ids == sorted_orm_fetched_sub_tasks

    @pytest.mark.parametrize(
        'ordering',
        ['task__project__user__password', 'task__project__user__id', 'task__project__user__is_superuser'])
    def test_get_sub_task_list_ordered_by_invalid_fields(self, ordering, task_instance, sub_task_create_batch,
                                                         active_user, request_factory):
        view = self.view_class.as_view({'get': 'list'})
        base_url = self.base_url.format(task_pk=task_instance.pk)
        url = f'{base_url}?{urlencode(query={"ordering": ordering})}'
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, task_pk=task_instance.pk)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] is not None

        response_result_ids = [record['id'] for record in response.data['results']]
        default_sorted_orm_fetched_sub_tasks = list(map(
            lambda uuid: str(uuid), get_all_sub_tasks_for_task(
                task=task_instance, task__project__user=active_user).values_list('id', flat=True)))
        assert response_result_ids == default_sorted_orm_fetched_sub_tasks

    def test_get_sub_task_detail(self, sub_task_instance, active_user, request_factory):
        url = self.detail_url.format(task_pk=sub_task_instance.task.pk, pk=sub_task_instance.pk)
        view = self.view_class.as_view({'get': 'retrieve'})
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, task_pk=sub_task_instance.task.pk, pk=sub_task_instance.pk)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(sub_task_instance.id)

    def test_get_someone_elses_sub_task_detail(self, sub_task_for_random_task, active_user, request_factory):
        url = self.detail_url.format(task_pk=sub_task_for_random_task.task.pk, pk=sub_task_for_random_task.pk)
        view = self.view_class.as_view({'get': 'retrieve'})
        request = request_factory.get(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, task_pk=sub_task_for_random_task.task.pk, pk=sub_task_for_random_task.pk)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_sub_task_with_valid_data(self, sub_task_data, sub_task_instance, active_user, request_factory):
        sub_task_data['task'] = sub_task_instance.task.id
        url = self.detail_url.format(task_pk=sub_task_instance.task.pk, pk=sub_task_instance.pk)
        view = self.view_class.as_view({'put': 'update'})
        request = request_factory.put(url, sub_task_data)
        force_authenticate(request=request, user=active_user)
        response = view(request, task_pk=sub_task_instance.task.pk, pk=sub_task_instance.pk)

        assert response.status_code == status.HTTP_200_OK
        assert response.data is not None
        assert all(key in response.data.keys() for key in sub_task_data.keys())

    @pytest.mark.parametrize(
        'invalid_field_key, invalid_field_value, get_field',
        [
            ('name', factory.Faker('pystr', max_chars=129).generate(), None),
            ('name', '', None),
            ('task', lazy_fixture('task_instance_for_random_project'), 'id'),
            ('task', '', None),
            ('is_completed', 123, None),
            ('is_completed', 'xyz', None),
        ]
    )
    def test_update_sub_task_with_invalid_data(self, invalid_field_key, invalid_field_value, get_field, sub_task_data,
                                               sub_task_instance, active_user, request_factory):
        sub_task_data['task'] = sub_task_instance.task.id
        if get_field is not None:
            sub_task_data[invalid_field_key] = getattr(invalid_field_value, get_field)
        else:
            sub_task_data[invalid_field_key] = invalid_field_value

        url = self.detail_url.format(task_pk=sub_task_instance.task.pk, pk=sub_task_instance.pk)
        view = self.view_class.as_view({'put': 'update'})
        request = request_factory.put(url, sub_task_data)
        force_authenticate(request=request, user=active_user)
        response = view(request, task_pk=sub_task_instance.task.pk, pk=sub_task_instance.pk)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert invalid_field_key in response.data

    def test_update_sub_task_with_duplicated_name(self, sub_task_data, sub_task_instance, sub_task_create_batch,
                                                  active_user, request_factory):
        sub_task_data['task'] = sub_task_instance.task.id
        sub_task_data['name'] = sub_task_create_batch[0].name
        url = self.detail_url.format(task_pk=sub_task_instance.task.pk, pk=sub_task_instance.pk)
        view = self.view_class.as_view({'put': 'update'})
        request = request_factory.put(url, sub_task_data)
        force_authenticate(request=request, user=active_user)
        response = view(request, task_pk=sub_task_instance.task.pk, pk=sub_task_instance.pk)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['name'][0] == SubTaskException.messages[SubTaskException.sub_task_duplicated]

    def test_update_someone_elses_sub_task(self, sub_task_data, sub_task_for_random_task, active_user, request_factory):
        sub_task_data['task'] = sub_task_for_random_task.task.id
        url = self.detail_url.format(task_pk=sub_task_for_random_task.task.pk, pk=sub_task_for_random_task.pk)
        view = self.view_class.as_view({'put': 'update'})
        request = request_factory.put(url, sub_task_data)
        force_authenticate(request=request, user=active_user)
        response = view(request, task_pk=sub_task_for_random_task.task.pk, pk=sub_task_for_random_task.pk)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_sub_task(self, sub_task_instance, active_user, request_factory):
        url = self.detail_url.format(task_pk=sub_task_instance.task.pk, pk=sub_task_instance.pk)
        view = self.view_class.as_view({'delete': 'destroy'})
        request = request_factory.delete(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, task_pk=sub_task_instance.task.pk, pk=sub_task_instance.pk)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_someone_elses_sub_task(self, sub_task_for_random_task, active_user, request_factory):
        url = self.detail_url.format(task_pk=sub_task_for_random_task.task.pk, pk=sub_task_for_random_task.pk)
        view = self.view_class.as_view({'delete': 'destroy'})
        request = request_factory.delete(url)
        force_authenticate(request=request, user=active_user)
        response = view(request, task_pk=sub_task_for_random_task.task.pk, pk=sub_task_for_random_task.pk)

        assert response.status_code == status.HTTP_404_NOT_FOUND
