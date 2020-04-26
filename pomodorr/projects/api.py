from rest_framework import filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from pomodorr.projects.selectors import ProjectSelector, PrioritySelector, TaskSelector
from pomodorr.projects.serializers import ProjectSerializer, PrioritySerializer, TaskSerializer
from pomodorr.tools.permissions import IsObjectOwner, IsTaskOwner


class PriorityViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = (IsAuthenticated, IsObjectOwner)
    serializer_class = PrioritySerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'priority_level', 'name']
    filterset_fields = {
        'priority_level': ['exact', 'gt', 'gte', 'lt', 'lte'],
        'name': ['exact', 'iexact', 'contains', 'icontains']
    }

    def get_queryset(self):
        return PrioritySelector.get_priorities_for_user(user=self.request.user)

    def get_serializer_context(self):
        context = {
            'request': self.request
        }

        return context


class ProjectsViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated, IsObjectOwner)
    serializer_class = ProjectSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'priority', 'user_defined_ordering', 'name']

    def get_queryset(self):
        return ProjectSelector.get_active_projects_for_user(user=self.request.user)

    def get_serializer_context(self) -> dict:
        context = {
            'request': self.request
        }
        return context


class TaskViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = (IsAuthenticated, IsTaskOwner)
    serializer_class = TaskSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'priority', 'user_defined_ordering', 'name']
    filterset_fields = {
        'priority': ['exact', 'gt', 'gte', 'lt', 'lte'],
        'name': ['exact', 'iexact', 'contains', 'icontains']
    }

    def get_queryset(self):
        return TaskSelector.get_all_non_removed_tasks_for_user(user=self.request.user)

    def get_serializer_context(self):
        context = {
            'request': self.request
        }

        return context
