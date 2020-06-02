from django.contrib import admin
from django.db import transaction

from pomodorr.projects.models import Project, Task, SubTask, Priority
from pomodorr.projects.selectors import ProjectSelector


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'priority', 'user_defined_ordering', 'is_removed')
    list_filter = ('is_removed',)
    actions = ['hard_delete', 'undo_delete']
    search_fields = ('user__username', 'name', 'color')

    def get_queryset(self, request):
        return ProjectSelector.get_all_projects()

    def undo_delete(modeladmin, request, queryset):
        with transaction.atomic():
            ProjectSelector.undo_delete_on_queryset(queryset=queryset)

    def hard_delete(modeladmin, request, queryset):
        with transaction.atomic():
            ProjectSelector.hard_delete_on_queryset(queryset=queryset)

    undo_delete.short_description = 'Undo deletion of selected projects'
    hard_delete.short_description = 'Delete objects entirely from database'


@admin.register(Priority)
class PriorityAdmin(admin.ModelAdmin):
    pass


@admin.register(SubTask)
class SubTaskAdmin(admin.ModelAdmin):
    pass


class SubTaskInlineAdmin(admin.StackedInline):
    model = SubTask


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    inlines = (SubTaskInlineAdmin,)
