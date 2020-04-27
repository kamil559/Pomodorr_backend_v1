from django.http import Http404
from rest_framework import filters
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from pomodorr.projects.selectors import ProjectSelector, PrioritySelector, TaskSelector, SubTaskSelector
from pomodorr.projects.serializers import ProjectSerializer, PrioritySerializer, TaskSerializer, SubTaskSerializer
from pomodorr.tools.permissions import IsObjectOwner, IsTaskOwner, IsSubTaskOwner


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
        return dict(request=self.request)


class ProjectsViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated, IsObjectOwner)
    serializer_class = ProjectSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'priority__priority_level', 'user_defined_ordering', 'name']
    filterset_fields = {
        'priority__priority_level': ['exact', 'gt', 'gte', 'lt', 'lte'],
        'name': ['exact', 'iexact', 'contains', 'icontains']
    }

    def get_queryset(self):
        return ProjectSelector.get_active_projects_for_user(user=self.request.user)

    def get_serializer_context(self) -> dict:
        return dict(request=self.request)


class TaskViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = (IsAuthenticated, IsTaskOwner)
    serializer_class = TaskSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'priority__priority_level', 'user_defined_ordering', 'name']
    filterset_fields = {
        'priority__priority_level': ['exact', 'gt', 'gte', 'lt', 'lte'],
        'name': ['exact', 'iexact', 'contains', 'icontains']
    }

    def get_queryset(self):
        return TaskSelector.get_all_non_removed_tasks_for_user(user=self.request.user)

    def get_serializer_context(self):
        return dict(request=self.request)


class SubTaskViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = (IsAuthenticated, IsSubTaskOwner)
    serializer_class = SubTaskSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'name', 'is_completed']
    filterset_fields = {
        'name': ['exact', 'iexact', 'contains', 'icontains'],
        'is_completed': ['exact']
    }

    def get_queryset(self):
        task_pk = self.kwargs.get('task_pk', None)
        if task_pk is not None:
            task = get_object_or_404(queryset=TaskSelector.get_all_non_removed_tasks(), pk=task_pk,
                                     project__user=self.request.user)
            return SubTaskSelector.get_all_sub_tasks_for_task(task=task)
        raise Http404

    def get_serializer_context(self):
        return dict(request=self.request)
