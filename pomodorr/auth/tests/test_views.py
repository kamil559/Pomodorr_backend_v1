import factory
import pytest
from django.urls import reverse

from pomodorr.auth.auth_views import custom_obtain_jwt_token, custom_verify_jwt_token
from pomodorr.tools.utils import get_time_delta

pytestmark = pytest.mark.django_db


class TestCustomObtainJSONWebToken:
    def test_custom_obtain_jwt_token_with_active_user(self, user_data, active_user, request_factory):
        obtain_jwt_token_url = reverse('api:token_obtain')

        request = request_factory.post(obtain_jwt_token_url, {
            'email': user_data.get('email'),
            'password': user_data.get('password')
        })
        response = custom_obtain_jwt_token(request)

        assert response.status_code == 200
        assert response.data.get('token') is not None

    def test_custom_obtain_jwt_token_with_blocked_user(self, blocked_user_data, blocked_user, request_factory):
        obtain_jwt_token_url = reverse('api:token_obtain')

        request = request_factory.post(obtain_jwt_token_url, {
            'email': blocked_user_data.get('email'),
            'password': blocked_user_data.get('password')
        })
        response = custom_obtain_jwt_token(request)

        assert response.status_code == 400
        assert response.data['non_field_errors'][0] == \
               "Your account is currently blocked. For further details contact the administration."


@pytest.mark.parametrize('view_url', [reverse('api:token_verify'), reverse('api:token_refresh')])
class TestCustomRefreshAndVerifyJSONWebToken:
    def test_custom_refresh_and_verify_jwt_token_with_valid_token(self, view_url, json_web_token, request_factory):
        request = request_factory.post(view_url, {
            'token': json_web_token
        })
        response = custom_verify_jwt_token(request)

        assert response.status_code == 200
        assert response.data.get('token') is not None

    def test_custom_refresh_and_verify_jwt_token_with_altered_user(self, view_url, json_web_token, request_factory,
                                                                   active_user):
        active_user.email = factory.Faker('email').generate()
        active_user.save()

        request = request_factory.post(view_url, {
            'token': json_web_token
        })
        response = custom_verify_jwt_token(request)

        assert response.status_code == 400
        assert response.data['non_field_errors'][0] == "User doesn't exist."

    def test_custom_refresh_and_verify_jwt_token_with_invalid_token(self, view_url, json_web_token, request_factory):
        request = request_factory.post(view_url, {
            'token': json_web_token + 'xyz'
        })
        response = custom_verify_jwt_token(request)

        assert response.status_code == 400
        assert response.data['non_field_errors'][0] == "Error decoding signature."

    def test_custom_refresh_and_verify_jwt_token_with_inactive_user(self, view_url, json_web_token, request_factory,
                                                                    active_user):
        active_user.is_active = False
        active_user.save()

        request = request_factory.post(view_url, {
            'token': json_web_token
        })
        response = custom_verify_jwt_token(request)

        assert response.status_code == 400
        assert response.data['non_field_errors'][0] == "User account is disabled."

    def test_custom_refresh_and_verify_jwt_token_with_blocked_user(self, view_url, json_web_token, request_factory,
                                                                   active_user):
        active_user.blocked_until = get_time_delta({"days": 1})
        active_user.save()

        request = request_factory.post(view_url, {
            'token': json_web_token
        })
        response = custom_verify_jwt_token(request)

        assert response.status_code == 400
        assert response.data['non_field_errors'][0] == \
               "Your account is currently blocked. For further details contact the administration."
