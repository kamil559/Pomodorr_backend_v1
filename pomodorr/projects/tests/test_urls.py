import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestPriorityUrls:
    def test_list_url(self):
        url = reverse('api:priority-list')
        assert url is not None

    def test_detail_url(self, priority_instance):
        url = reverse('api:priority-detail', kwargs={
            'pk': priority_instance.pk
        })
        assert url is not None


class TestProjectUrls:
    def test_list_url(self):
        url = reverse('api:project-list')
        assert url is not None

    def test_detail_url(self, project_instance):
        url = reverse('api:project-detail', kwargs={
            'pk': project_instance.pk
        })
        assert url is not None


class TestTaskUrls:
    def test_list_url(self):
        url = reverse('api:task-list')
        assert url is not None

    def test_detail_url(self, task_instance):
        url = reverse('api:task-detail', kwargs={
            'pk': task_instance.pk
        })
        assert url is not None


class TestSubTaskUrls:
    def test_list_url(self, task_instance):
        url = reverse('api:sub_task-list')
        assert url is not None

    def test_detail_url(self, sub_task_instance):
        url = reverse('api:task-detail', kwargs={
            'pk': sub_task_instance.pk,
        })
        assert url is not None
