from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from pomodorr.frames.filtersets import DataFrameIsFinishedFilter
from pomodorr.frames.models import DateFrame
from pomodorr.frames.selectors import DateFrameSelector
from pomodorr.frames.serializers import DateFrameSerializer
from pomodorr.tools.permissions import IsDateFrameOwner


class DateFrameListView(GenericViewSet, ListModelMixin):
    permission_classes = (IsAuthenticated, IsDateFrameOwner)
    serializer_class = DateFrameSerializer
    filter_backends = [OrderingFilter, DjangoFilterBackend]
    ordering_fields = ['created', 'duration', 'is_finished']
    filterset_class = DataFrameIsFinishedFilter

    date_frame_selector = DateFrameSelector(model_class=DateFrame)

    def get_queryset(self):
        return self.date_frame_selector.get_all_date_frames_for_user(user=self.request.user)

    def get_serializer_context(self):
        return dict(request=self.request)
