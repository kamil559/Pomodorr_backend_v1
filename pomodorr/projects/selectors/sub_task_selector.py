from pomodorr.projects.models import SubTask


def get_all_sub_tasks(**kwargs):
    return SubTask.objects.all(**kwargs)


def get_all_sub_tasks_for_task(task, **kwargs):
    return SubTask.objects.filter(task=task, **kwargs)


def get_all_sub_tasks_for_user(user, **kwargs):
    return SubTask.objects.filter(task__project__user__id=user.id, **kwargs)
