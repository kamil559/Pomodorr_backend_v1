import factory
import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from rest_framework.test import APIClient
from rest_framework_jwt.serializers import jwt_payload_handler, jwt_encode_handler

from pomodorr.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def request_factory() -> RequestFactory:
    return RequestFactory()


@pytest.fixture
def client():
    client = APIClient()
    return client


@pytest.fixture
def user_data():
    return factory.build(dict, FACTORY_CLASS=UserFactory)


@pytest.fixture
def active_user(user_data):
    return UserFactory.create(**user_data, is_active=True)


@pytest.fixture
def non_active_user():
    return UserFactory.create()


@pytest.fixture(scope="session")
def user_model():
    return get_user_model()


@pytest.fixture()
def auth(active_user, client):
    jwt_payload = jwt_payload_handler(active_user)
    json_web_token = jwt_encode_handler(jwt_payload)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {json_web_token}")
