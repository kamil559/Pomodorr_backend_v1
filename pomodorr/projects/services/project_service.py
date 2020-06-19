from django.contrib.auth.models import AbstractUser

from pomodorr.projects.selectors.project_selector import get_active_projects_for_user


def is_project_name_available(user: AbstractUser, name: str, excluded=None) -> bool:
    query = get_active_projects_for_user(user=user, name=name)
    if excluded is not None:
        return not query.exclude(id=excluded.id).exists()
    return not query.exists()
