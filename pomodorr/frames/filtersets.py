from django_filters import rest_framework as filters

from pomodorr.frames.models import DateFrame


class DataFrameIsFinishedFilter(filters.FilterSet):
    is_finished = filters.BooleanFilter(field_name='is_finished')

    class Meta:
        model = DateFrame
        fields = {
            'task__id': ['exact'],
            'created': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'frame_type': ['exact'],
            'is_finished': ['exact']
        }
