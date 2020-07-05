from django.conf import settings
from django.urls import path, include
from rest_framework.routers import DefaultRouter, SimpleRouter

from pomodorr.auth.auth_views import custom_obtain_jwt_token, custom_refresh_jwt_token, custom_verify_jwt_token
from pomodorr.frames.api import DateFrameListView
from pomodorr.projects.api import ProjectViewSet, PriorityViewSet, TaskViewSet, SubTaskViewSet

app_name = "api"

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register(r'priorities', PriorityViewSet, basename='priority')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'sub_tasks', SubTaskViewSet, basename='sub_task')
router.register(r'date_frames', DateFrameListView, basename='date_frame')

urlpatterns = router.urls

urlpatterns += [
    # djoser auth
    path("auth/", include('djoser.urls')),
    path("auth/", include('djoser.urls.authtoken')),

    # jwt auth
    path('auth/jwt/create/', custom_obtain_jwt_token, name="token_obtain"),
    path('auth/jwt/refresh/', custom_refresh_jwt_token, name="token_refresh"),
    path('auth/jwt/verify/', custom_verify_jwt_token, name="token_verify"),
]
