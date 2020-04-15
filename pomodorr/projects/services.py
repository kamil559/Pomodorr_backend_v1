from typing import Union

from model_utils.managers import SoftDeletableQuerySetMixin

from pomodorr.projects.models import Project, CustomProfileQueryset


class ProjectDomainModel:
    model = Project

    @classmethod
    def get_active_projects_for_user(cls, user):
        return cls.model.objects.filter(user=user)

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
    def hard_delete_on_subset(cls, queryset: Union[CustomProfileQueryset, SoftDeletableQuerySetMixin]) -> None:
        queryset.delete(soft=False)

    @classmethod
    def undo_delete_on_queryset(cls, queryset: Union[CustomProfileQueryset, SoftDeletableQuerySetMixin]) -> None:
        queryset.update(is_removed=False)
