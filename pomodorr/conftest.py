import random
from datetime import timedelta
from unittest.mock import Mock

import factory
import pytest
from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework_jwt.serializers import jwt_payload_handler, jwt_encode_handler

from pomodorr.projects.admin import ProjectAdmin
from pomodorr.projects.models import Project, Priority, Task, SubTask, TaskEvent
from pomodorr.projects.services import TaskServiceModel
from pomodorr.projects.tests.factories import ProjectFactory, PriorityFactory, TaskFactory, SubTaskFactory, \
    TaskEventFactory
from pomodorr.tools.utils import get_time_delta
from pomodorr.users.admin import IsBlockedFilter, UserAdmin
from pomodorr.users.tests.factories import UserFactory, AdminFactory, prepare_registration_data


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def request_factory() -> APIRequestFactory:
    return APIRequestFactory()


@pytest.fixture
def user_data():
    return factory.build(dict, FACTORY_CLASS=UserFactory)


@pytest.fixture
def non_active_user_data():
    return factory.build(dict, FACTORY_CLASS=UserFactory)


@pytest.fixture
def blocked_user_data():
    return factory.build(dict, FACTORY_CLASS=UserFactory)


@pytest.fixture
def admin_data():
    return factory.build(dict, FACTORY_CLASS=AdminFactory)


@pytest.fixture
def user_registration_data():
    registration_dict = prepare_registration_data()
    registration_dict['password1'] = registration_dict.pop('password')
    return registration_dict


@pytest.fixture
def active_user(user_data):
    return UserFactory.create(**user_data, is_active=True)


@pytest.fixture
def non_active_user(non_active_user_data):
    return UserFactory.create(**non_active_user_data)


@pytest.fixture
def admin_user(admin_data):
    return AdminFactory.create(**admin_data)


@pytest.fixture
def blocked_user(blocked_user_data):
    return UserFactory.create(is_active=True, blocked_until=get_time_delta({"days": 1}), **blocked_user_data)


@pytest.fixture
def ready_to_unblock_user():
    return UserFactory.create(is_active=True, blocked_until=get_time_delta({"days": 1}, ahead=False))


@pytest.fixture(scope="session")
def user_model():
    return get_user_model()


@pytest.fixture
def request_mock():
    request = Mock()
    return request


@pytest.fixture
def is_blocked_filter(user_model, request_mock) -> IsBlockedFilter:
    props = vars(IsBlockedFilter)
    is_blocked_filter = IsBlockedFilter(request=request_mock, params=props, model=user_model, model_admin=UserAdmin)
    return is_blocked_filter


@pytest.fixture
def user_admin_queryset(user_model, request_mock) -> IsBlockedFilter:
    site = AdminSite()
    user_admin = UserAdmin(model=user_model, admin_site=site)
    user_admin_queryset = user_admin.get_queryset(request=request_mock)
    return user_admin_queryset


@pytest.fixture
def json_web_token(active_user):
    jwt_payload = jwt_payload_handler(active_user)
    json_web_token = jwt_encode_handler(jwt_payload)
    return json_web_token


@pytest.fixture
def client():
    client = APIClient()
    return client


@pytest.fixture
def auth(json_web_token, client):
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {json_web_token}")
    return json_web_token


@pytest.fixture(scope='session')
def project_model():
    return Project


@pytest.fixture
def project_data():
    return factory.build(dict, FACTORY_CLASS=ProjectFactory)


@pytest.fixture
def project_instance(active_user):
    return factory.create(klass=ProjectFactory, user=active_user)


@pytest.fixture
def second_project_instance(active_user):
    yield factory.create(klass=ProjectFactory, user=active_user)


@pytest.fixture
def project_instance_removed(active_user):
    return factory.create(klass=ProjectFactory, user=active_user, is_removed=True)


@pytest.fixture
def project_instance_for_random_user():
    return factory.create(klass=ProjectFactory, user=UserFactory.create(is_active=True))


@pytest.fixture
def project_create_batch(active_user):
    return factory.create_batch(klass=ProjectFactory, size=5, user=active_user)


@pytest.fixture
def removed_project_create_batch(active_user):
    return factory.create_batch(klass=ProjectFactory, size=5, user=active_user, is_removed=True)


@pytest.fixture
def project_admin_view(project_model):
    site = AdminSite()
    return ProjectAdmin(model=project_model, admin_site=site)


@pytest.fixture(scope='session')
def priority_model():
    return Priority


@pytest.fixture
def priority_data():
    return factory.build(dict, FACTORY_CLASS=PriorityFactory)


@pytest.fixture
def priority_instance(active_user):
    return factory.create(klass=PriorityFactory, user=active_user)


@pytest.fixture
def priority_create_batch(active_user):
    return factory.create_batch(klass=PriorityFactory, size=5, user=active_user)


@pytest.fixture
def priority_instance_for_random_user():
    return factory.create(klass=PriorityFactory, user=UserFactory.create(is_active=True))


@pytest.fixture
def random_priority_id(priority_instance_for_random_user):
    return priority_instance_for_random_user.id


@pytest.fixture(scope='session')
def task_model():
    return Task


@pytest.fixture
def task_data():
    return factory.build(dict, FACTORY_CLASS=TaskFactory)


@pytest.fixture
def task_instance(priority_instance, project_instance):
    return factory.create(klass=TaskFactory, priority=priority_instance, project=project_instance)


@pytest.fixture
def completed_task_instance(task_model, priority_instance, project_instance):
    return factory.create(klass=TaskFactory, priority=priority_instance, project=project_instance,
                          status=task_model.status_completed)


@pytest.fixture
def repeatable_task_instance(priority_instance, project_instance):
    return factory.create(klass=TaskFactory, priority=priority_instance, project=project_instance,
                          due_date=timezone.now(), repeat_duration=timedelta(days=random.randint(1, 5)))


@pytest.fixture
def repeatable_task_instance_without_due_date(priority_instance, project_instance):
    return factory.create(klass=TaskFactory, priority=priority_instance, project=project_instance,
                          repeat_duration=timedelta(days=random.randint(1, 5)))


@pytest.fixture
def task_instance_in_second_project(second_project_instance, priority_instance, project_instance):
    return factory.create(klass=TaskFactory, priority=priority_instance, project=second_project_instance)


@pytest.fixture
def duplicate_task_instance_in_second_project(task_instance, second_project_instance, priority_instance,
                                              project_instance):
    return factory.create(klass=TaskFactory, priority=priority_instance, project=second_project_instance,
                          name=task_instance.name)


@pytest.fixture
def task_instance_completed(priority_instance, project_instance):
    return factory.create(klass=TaskFactory, priority=priority_instance, project=project_instance, status=1)


@pytest.fixture
def task_instance_removed(priority_instance, project_instance):
    return factory.create(klass=TaskFactory, priority=priority_instance, project=project_instance, is_removed=True)


@pytest.fixture()
def task_instance_for_random_project(project_instance_for_random_user):
    return factory.create(klass=TaskFactory, project=project_instance_for_random_user)


@pytest.fixture(scope='session')
def sub_task_model():
    return SubTask


@pytest.fixture
def sub_task_data():
    return factory.build(dict, FACTORY_CLASS=SubTaskFactory)


@pytest.fixture
def sub_task_instance(task_instance):
    return factory.create(klass=SubTaskFactory, task=task_instance)


@pytest.fixture
def sub_task_for_random_task(task_instance_for_random_project):
    return factory.create(klass=SubTaskFactory, task=task_instance_for_random_project)


@pytest.fixture(scope='class')
def task_service_model():
    return TaskServiceModel()


@pytest.fixture(scope='session')
def task_event_model():
    return TaskEvent


@pytest.fixture
def task_event_data():
    return factory.build(dict, FACTORY_CLASS=TaskEventFactory)


@pytest.fixture
def task_event_instance(task_instance):
    return factory.create(klass=TaskEventFactory, task=task_instance)


@pytest.fixture
def task_event_create_batch(task_instance):
    return factory.create_batch(klass=TaskEventFactory, size=5, task=task_instance)


@pytest.fixture
def task_event_for_random_task(task_instance_for_random_project):
    return factory.create(klass=TaskEventFactory, task=task_instance_for_random_project)


@pytest.fixture
def task_event_in_progress(task_instance):
    return factory.create(klass=TaskEventFactory, task=task_instance, end=None)
