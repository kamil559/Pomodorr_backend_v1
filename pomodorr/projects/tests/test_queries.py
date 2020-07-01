import factory
import pytest
from django.db.models import Count
from django.utils.http import urlencode

pytestmark = pytest.mark.django_db


class TestPriorityViewSetQueries:
    base_url = '/api/priorities/'
    detail_url = '/api/priorities/{pk}/'

    def test_priority_detail_view(self, client, django_assert_num_queries, active_user, priority_instance):
        client.force_authenticate(user=active_user)

        with django_assert_num_queries(1):
            client.get(self.detail_url.format(pk=priority_instance.pk))

    def test_priority_list_view(self, client, django_assert_num_queries, active_user, priority_create_batch):
        client.force_authenticate(user=active_user)
        with django_assert_num_queries(2):
            client.get(self.base_url)

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
    def test_priority_list_view_filter(self, filter_lookup, client, django_assert_max_num_queries, active_user,
                                       priority_create_batch):
        url = f'{self.base_url}?{urlencode(query=filter_lookup)}'
        client.force_authenticate(user=active_user)
        with django_assert_max_num_queries(2):
            client.get(url)

    def test_priority_create_view(self, client, django_assert_num_queries, active_user, priority_data):
        initial_priorities_count = active_user.priorities.count()

        client.force_authenticate(user=active_user)
        with django_assert_num_queries(2):
            client.post(self.base_url, data=priority_data)
        assert initial_priorities_count < active_user.priorities.count()

    def test_priority_update_view(self, client, django_assert_num_queries, active_user, priority_instance,
                                  priority_data):
        priority_data['color'] = factory.Faker('color').generate()

        client.force_authenticate(user=active_user)
        with django_assert_num_queries(3):
            client.put(self.detail_url.format(pk=priority_instance.pk), data=priority_data)


class TestProjectViewSetQueries:
    base_url = '/api/projects/'
    detail_url = '/api/projects/{pk}/'

    def test_project_detail_view(self, client, django_assert_num_queries, active_user, project_instance):
        client.force_authenticate(user=active_user)

        with django_assert_num_queries(1):
            client.get(self.detail_url.format(pk=project_instance.pk))

    def test_project_list_view(self, client, django_assert_num_queries, active_user, project_create_batch):
        client.force_authenticate(user=active_user)
        with django_assert_num_queries(2):
            client.get(self.base_url)

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
    def test_project_list_view_filter(self, filter_lookup, client, django_assert_max_num_queries, active_user,
                                      project_create_batch):
        url = f'{self.base_url}?{urlencode(query=filter_lookup)}'
        client.force_authenticate(user=active_user)
        with django_assert_max_num_queries(2):
            client.get(url)

    def test_project_create_view(self, client, django_assert_num_queries, active_user, project_data):
        initial_projects_count = active_user.projects.count()

        client.force_authenticate(user=active_user)
        with django_assert_num_queries(2):
            client.post(self.base_url, data=project_data)
        assert initial_projects_count < active_user.projects.count()

    def test_project_update_view(self, client, django_assert_num_queries, active_user, project_instance,
                                 project_data):
        project_data['name'] = factory.Faker('name').generate()

        client.force_authenticate(user=active_user)
        with django_assert_num_queries(3):
            client.put(self.detail_url.format(pk=project_instance.pk), data=project_data)


class TestTaskViewSetQueries:
    base_url = '/api/tasks/'
    detail_url = '/api/tasks/{pk}/'

    def test_task_detail_view(self, client, django_assert_num_queries, active_user, task_instance,
                              sub_task_create_batch):
        client.force_authenticate(user=active_user)

        with django_assert_num_queries(2):
            client.get(self.detail_url.format(pk=task_instance.pk))

    def test_task_list_view(self, client, django_assert_num_queries, active_user, task_instance_create_batch):
        client.force_authenticate(user=active_user)
        with django_assert_num_queries(3):
            client.get(self.base_url)

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
    def test_task_list_view_filter(self, filter_lookup, client, django_assert_max_num_queries, active_user,
                                   task_instance_create_batch):
        url = f'{self.base_url}?{urlencode(query=filter_lookup)}'
        client.force_authenticate(user=active_user)
        with django_assert_max_num_queries(3):
            client.get(url)

    def test_task_create_view(self, client, django_assert_num_queries, active_user, project_instance, task_data):
        initial_tasks_count = active_user.projects.aggregate(Count('tasks'))['tasks__count']
        task_data['project'] = str(project_instance.pk)

        client.force_authenticate(user=active_user)

        with django_assert_num_queries(6):
            client.post(self.base_url, data=task_data)
        assert initial_tasks_count < active_user.projects.aggregate(Count('tasks'))['tasks__count']

    def test_task_update_view(self, client, django_assert_num_queries, active_user, task_instance,
                              task_data):
        task_data['note'] = factory.Faker('text').generate()

        client.force_authenticate(user=active_user)
        with django_assert_num_queries(2):
            client.put(self.detail_url.format(pk=task_instance.pk), data=task_data)


class TestSubTaskViewSetQueries:
    base_url = '/api/sub_tasks/'
    detail_url = '/api/sub_tasks/{pk}/'

    def test_sub_task_detail_view(self, client, django_assert_num_queries, active_user, sub_task_instance):
        client.force_authenticate(user=active_user)

        with django_assert_num_queries(1):
            client.get(self.detail_url.format(pk=sub_task_instance.pk))

    def test_sub_task_list_view(self, client, django_assert_num_queries, active_user, sub_task_create_batch):
        client.force_authenticate(user=active_user)
        with django_assert_num_queries(2):
            client.get(self.base_url)

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
    def test_sub_task_list_view_filter(self, filter_lookup, client, django_assert_max_num_queries, active_user,
                                       sub_task_create_batch):
        url = f'{self.base_url}?{urlencode(query=filter_lookup)}'
        client.force_authenticate(user=active_user)
        with django_assert_max_num_queries(2):
            client.get(url)

    def test_sub_task_create_view(self, client, django_assert_num_queries, active_user, task_instance, sub_task_data):
        initial_sub_tasks_count = active_user.projects.aggregate(Count('tasks__sub_tasks', distinct=True))[
            'tasks__sub_tasks__count']
        sub_task_data['task'] = str(task_instance.pk)

        client.force_authenticate(user=active_user)
        with django_assert_num_queries(4):
            client.post(self.base_url, data=sub_task_data)
            print()
        assert initial_sub_tasks_count < active_user.projects.aggregate(Count('tasks__sub_tasks', distinct=True))[
            'tasks__sub_tasks__count']

    def test_sub_task_update_view(self, client, django_assert_num_queries, active_user, task_instance,
                                  sub_task_instance, sub_task_data):
        sub_task_data['task'] = str(task_instance.pk)
        sub_task_data['name'] = factory.Faker('name').generate()

        client.force_authenticate(user=active_user)
        with django_assert_num_queries(3):
            client.put(self.detail_url.format(pk=sub_task_instance.pk), data=sub_task_data)

