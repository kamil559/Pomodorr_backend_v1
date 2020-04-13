from rest_framework import filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from pomodorr.projects.serializers import ProjectSerializer
from pomodorr.projects.services import ProjectDomainModel
from pomodorr.tools.permissions import IsObjectOwner


class ProjectsViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated, IsObjectOwner)
    serializer_class = ProjectSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'priority', 'user_defined_ordering']

    def get_queryset(self):
        return ProjectDomainModel.get_active_projects_for_user(user=self.request.user)

    def get_serializer_context(self) -> dict:
        context = {
            'request': self.request
        }
        return context
