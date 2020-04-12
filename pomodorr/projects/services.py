from pomodorr.projects.models import Project


class ProjectDomainModel:
    DB_MODEL = Project

    @classmethod
    def get_active_projects_for_user(cls, user):
        return cls.DB_MODEL.objects.filter(user=user)
