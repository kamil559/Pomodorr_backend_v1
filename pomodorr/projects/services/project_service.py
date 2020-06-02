from django.contrib.auth.models import AbstractUser

from pomodorr.projects.selectors.project_selector import get_active_projects_for_user


def is_project_name_available(user: AbstractUser, name: str, exclude=None) -> bool:
    query = get_active_projects_for_user(user=user, name=name)
    if exclude is not None:
        return not query.exclude(id=exclude.id).exists()
    return not query.exists()
