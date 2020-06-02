from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from pomodorr.frames.filtersets import DataFrameIsFinishedFilter
from pomodorr.frames.selectors.date_frame_selector import get_all_date_frames_for_user
from pomodorr.frames.serializers import DateFrameSerializer
from pomodorr.tools.permissions import IsDateFrameOwner


class DateFrameListView(GenericViewSet, ListModelMixin):
    permission_classes = (IsAuthenticated, IsDateFrameOwner)
    serializer_class = DateFrameSerializer
    filter_backends = [OrderingFilter, DjangoFilterBackend]
    ordering_fields = ['created', 'duration', 'is_finished']
    filterset_class = DataFrameIsFinishedFilter


    def get_queryset(self):
        return get_all_date_frames_for_user(user=self.request.user)

    def get_serializer_context(self):
        return dict(request=self.request)
