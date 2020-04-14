from django.contrib import admin
from django.db import transaction

from pomodorr.projects.models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'priority', 'user_defined_ordering', 'is_removed')
    list_filter = ('is_removed',)
    actions = ['hard_delete', 'undo_delete']
    search_fields = ('user__username', 'name', 'color')

    def get_queryset(self, request):
        return self.model.all_objects.all()

    def undo_delete(modeladmin, request, queryset):
        with transaction.atomic():
            queryset.update(is_removed=False)

    def hard_delete(modeladmin, request, queryset):
        with transaction.atomic():
            queryset.delete(soft=False)

    undo_delete.short_description = 'Undo deletion of selected projects'
    hard_delete.short_description = 'Delete objects entirely from database'
