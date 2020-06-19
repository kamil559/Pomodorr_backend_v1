from rest_framework_jwt.views import JSONWebTokenAPIView

from pomodorr.auth.auth_serializers import (
    CustomJSONWebTokenSerializer, CustomRefreshJSONWebTokenSerializer, CustomVerifyJSONWebTokenSerializer
)


class CustomObtainJSONWebToken(JSONWebTokenAPIView):
    serializer_class = CustomJSONWebTokenSerializer


class CustomRefreshJSONWebToken(JSONWebTokenAPIView):
    serializer_class = CustomRefreshJSONWebTokenSerializer


class CustomVerifyJSONWebToken(JSONWebTokenAPIView):
    serializer_class = CustomVerifyJSONWebTokenSerializer


custom_obtain_jwt_token = CustomObtainJSONWebToken.as_view()
custom_refresh_jwt_token = CustomRefreshJSONWebToken.as_view()
custom_verify_jwt_token = CustomVerifyJSONWebToken.as_view()
