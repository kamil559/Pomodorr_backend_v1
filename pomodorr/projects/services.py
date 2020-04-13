from pomodorr.projects.models import Project


class ProjectDomainModel:
    model = Project

    @classmethod
    def get_active_projects_for_user(cls, user):
        return cls.model.objects.filter(user=user)
