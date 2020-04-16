from typing import Union

from model_utils.managers import SoftDeletableQuerySetMixin

from pomodorr.projects.models import Project, CustomSoftDeletableQueryset, Priority


class ProjectDomainModel:
    model = Project

    @classmethod
    def get_active_projects_for_user(cls, user, **kwargs):
        return cls.model.objects.filter(user=user, **kwargs)

    @classmethod
    def get_removed_projects_for_user(cls, user):
        return cls.model.all_objects.filter(is_removed=True, user=user)

    @classmethod
    def get_all_projects_for_user(cls, user):
        return cls.model.all_objects.filter(user=user)

    @classmethod
    def get_all_active_projects(cls):
        return cls.model.objects.all()

    @classmethod
    def get_all_removed_projects(cls):
        return cls.model.all_objects.filter(is_removed=True)

    @classmethod
    def get_all_projects(cls):
        return cls.model.all_objects.all()

    @classmethod
    def hard_delete_on_queryset(cls, queryset: Union[CustomSoftDeletableQueryset, SoftDeletableQuerySetMixin]) -> None:
        queryset.delete(soft=False)

    @classmethod
    def undo_delete_on_queryset(cls, queryset: Union[CustomSoftDeletableQueryset, SoftDeletableQuerySetMixin]) -> None:
        queryset.update(is_removed=False)


class PriorityDomainModel:

    @classmethod
    def get_all_priorities(cls):
        return Priority.objects.all()

    @classmethod
    def get_priorities_for_user(cls, user):
        return Priority.objects.filter(user=user)
