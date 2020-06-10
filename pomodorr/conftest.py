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

from pomodorr.frames.admin import IsFinishedFilter, DateFrameAdmin
from pomodorr.frames.models import DateFrame
from pomodorr.frames.tests.factories import DateFrameFactory, InnerDateFrameFactory
from pomodorr.projects.admin import ProjectAdmin
from pomodorr.projects.models import Project, Priority, Task, SubTask
from pomodorr.projects.tests.factories import ProjectFactory, PriorityFactory, TaskFactory, SubTaskFactory
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
def request_mock(active_user):
    request = Mock()
    request.user = active_user
    return request


@pytest.fixture
def is_blocked_filter(user_model, request_mock) -> IsBlockedFilter:
    props = vars(IsBlockedFilter)
    is_blocked_filter = IsBlockedFilter(request=request_mock, params=props, model=user_model, model_admin=UserAdmin)
    return is_blocked_filter


@pytest.fixture
def user_admin_queryset(user_model, request_mock):
    site = AdminSite()
    user_admin = UserAdmin(model=user_model, admin_site=site)
    user_admin_queryset = user_admin.get_queryset(request=request_mock)
    return user_admin_queryset


@pytest.fixture
def is_finished_filter(date_frame_model, request_mock) -> IsFinishedFilter:
    is_finished_filter = IsFinishedFilter(request=request_mock, params=vars(IsFinishedFilter),
                                          model=date_frame_model, model_admin=DateFrameAdmin)
    return is_finished_filter


@pytest.fixture
def date_frame_admin_queryset(date_frame_model, request_mock):
    site = AdminSite()
    date_frame_admin = DateFrameAdmin(model=date_frame_model, admin_site=site)
    date_frame_admin_queryset = date_frame_admin.get_queryset(request=request_mock)
    return date_frame_admin_queryset


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
    return factory.create(klass=ProjectFactory, user=active_user)


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
def task_instance_create_batch(priority_instance, project_instance):
    return factory.create_batch(klass=TaskFactory, size=5, priority=priority_instance, project=project_instance)


@pytest.fixture
def completed_task_instance(task_model, priority_instance, project_instance):
    return factory.create(klass=TaskFactory, priority=priority_instance, project=project_instance,
                          status=task_model.status_completed)


@pytest.fixture
def repeatable_task_instance(priority_instance, project_instance):
    return factory.create(klass=TaskFactory, priority=priority_instance, project=project_instance,
                          due_date=timezone.now(), repeat_duration=timedelta(days=random.randint(1, 5)))


@pytest.fixture
def completed_repeatable_task_instance(task_model, priority_instance, project_instance):
    return factory.create(klass=TaskFactory, priority=priority_instance, project=project_instance,
                          due_date=timezone.now(), repeat_duration=timedelta(days=random.randint(1, 5)),
                          status=task_model.status_completed)


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
def sub_task_create_batch(task_instance):
    return factory.create_batch(klass=SubTaskFactory, size=5, task=task_instance)


@pytest.fixture
def sub_task_for_random_task(task_instance_for_random_project):
    return factory.create(klass=SubTaskFactory, task=task_instance_for_random_project)


@pytest.fixture(scope='session')
def date_frame_model():
    return DateFrame


@pytest.fixture
def date_frame_data():
    return factory.build(dict, FACTORY_CLASS=DateFrameFactory)


@pytest.fixture
def date_frame_instance(task_instance):
    return factory.create(klass=DateFrameFactory, task=task_instance)


@pytest.fixture
def date_frame_create_batch(task_instance):
    return factory.create_batch(klass=InnerDateFrameFactory, size=5, task=task_instance)


@pytest.fixture
def date_frame_create_batch_for_second_project(task_instance_in_second_project):
    return factory.create_batch(klass=InnerDateFrameFactory, size=5, task=task_instance_in_second_project)


@pytest.fixture
def date_frame_for_random_task(task_instance_for_random_project):
    return factory.create(klass=DateFrameFactory, task=task_instance_for_random_project)


@pytest.fixture
def date_frame_in_progress(task_instance):
    return factory.create(klass=DateFrameFactory, task=task_instance, end=None)


@pytest.fixture
def pomodoro_in_progress_with_breaks(task_instance):
    pomodoro_date_frame = factory.create(klass=DateFrameFactory, task=task_instance, end=None, frame_type=0)
    factory.create(klass=InnerDateFrameFactory, task=task_instance, frame_type=1, start=get_time_delta({'minutes': 3}),
                   end=get_time_delta({'minutes': 5}))
    factory.create(klass=InnerDateFrameFactory, task=task_instance, frame_type=1, start=get_time_delta({'minutes': 6}),
                   end=get_time_delta({'minutes': 10}))
    return pomodoro_date_frame


@pytest.fixture
def pomodoro_in_progress_with_pauses(task_instance):
    pomodoro_date_frame = factory.create(klass=DateFrameFactory, task=task_instance, end=None, frame_type=0)
    factory.create(klass=InnerDateFrameFactory, task=task_instance, frame_type=2, start=get_time_delta({'minutes': 3}),
                   end=get_time_delta({'minutes': 5}))
    factory.create(klass=InnerDateFrameFactory, task=task_instance, frame_type=2, start=get_time_delta({'minutes': 6}),
                   end=get_time_delta({'minutes': 10}))
    return pomodoro_date_frame


@pytest.fixture
def pomodoro_in_progress_with_breaks_and_pauses(task_instance):
    pomodoro_date_frame = factory.create(klass=DateFrameFactory, task=task_instance, end=None, frame_type=0)
    factory.create(klass=InnerDateFrameFactory, task=task_instance, frame_type=1,
                   start=get_time_delta({'minutes': 2}), end=get_time_delta({'minutes': 4}))
    factory.create(klass=InnerDateFrameFactory, task=task_instance, frame_type=1,
                   start=get_time_delta({'minutes': 5}), end=get_time_delta({'minutes': 7}))
    factory.create(klass=InnerDateFrameFactory, task=task_instance, frame_type=2,
                   start=get_time_delta({'minutes': 10}), end=get_time_delta({'minutes': 12}))
    factory.create(klass=InnerDateFrameFactory, task=task_instance, frame_type=2,
                   start=get_time_delta({'minutes': 15}), end=get_time_delta({'minutes': 19}))
    return pomodoro_date_frame


@pytest.fixture
def pomodoro_in_progress(task_instance):
    return factory.create(klass=DateFrameFactory, task=task_instance, end=None, frame_type=0)


@pytest.fixture
def break_in_progress(task_instance):
    return factory.create(klass=DateFrameFactory, task=task_instance, end=None, frame_type=1)


@pytest.fixture
def pause_in_progress(task_instance):
    return factory.create(klass=DateFrameFactory, task=task_instance, end=None, frame_type=2)


@pytest.fixture
def pause_in_progress_with_ongoing_pomodoro(task_instance):
    pomodoro_in_progress = factory.create(klass=DateFrameFactory, task=task_instance, end=None, frame_type=0)
    pause_in_progress = factory.create(klass=DateFrameFactory, task=task_instance, end=None, frame_type=2)
    return pause_in_progress, pomodoro_in_progress


@pytest.fixture
def date_frame_in_progress_for_yesterday(task_instance):
    date_frame_instance = factory.create(klass=DateFrameFactory, task=task_instance,
                                         start=get_time_delta({'days': 1}, ahead=False), end=None)
    return date_frame_instance


@pytest.fixture
def obsolete_date_frames(task_instance):
    obsolete_pomodoro = factory.create(klass=DateFrameFactory, task=task_instance,
                                       start=get_time_delta({'days': 8}, ahead=False),
                                       frame_type=0, end=None)
    obsolete_break = factory.create(klass=DateFrameFactory, task=task_instance,
                                    start=get_time_delta({'days': 8}, ahead=False),
                                    frame_type=1, end=None)
    obsolete_pause = factory.create(klass=DateFrameFactory, task=task_instance,
                                    start=get_time_delta({'days': 8}, ahead=False),
                                    frame_type=2, end=None)
    return obsolete_pomodoro, obsolete_break, obsolete_pause
