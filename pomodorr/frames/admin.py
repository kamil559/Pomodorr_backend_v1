from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from pomodorr.frames.models import DateFrame
from pomodorr.frames.selectors.date_frame_selector import get_all_date_frames


class IsFinishedFilter(admin.SimpleListFilter):
    title = 'is_finished status'
    parameter_name = 'is_finished'

    lookup_choices = (
        ('1', _('Yes')),
        ('0', _('No'))
    )

    def lookups(self, request, model_admin):
        return self.lookup_choices

    def queryset(self, request, queryset):
        value = self.value()

        if value == self.lookup_choices[0][0]:
            return queryset.filter(is_finished=True)
        elif value == self.lookup_choices[1][0]:
            return queryset.filter(is_finished=False)
        return queryset


@admin.register(DateFrame)
class DateFrameAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'frame_type', 'start', 'end', 'duration', 'task', 'is_finished')
    fieldsets = [
        (None, {'fields': ['start', 'end', 'frame_type', 'task']}),
    ]
    search_fields = ('frame_type', 'task__name', 'start', 'end')
    list_filter = ('frame_type', IsFinishedFilter)

    def get_queryset(self, request):
        return get_all_date_frames()

    def is_finished(self, instance):
        return instance.is_finished

    is_finished.boolean = True
    is_finished.admin_order_field = 'is_finished'
