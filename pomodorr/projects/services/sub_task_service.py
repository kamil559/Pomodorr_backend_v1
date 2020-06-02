from pomodorr.projects.selectors.sub_task_selector import get_all_sub_tasks_for_task


def is_sub_task_name_available(task, name: str, exclude=None) -> bool:
    query = get_all_sub_tasks_for_task(task=task, name=name)
    if exclude is not None:
        return not query.exclude(id=exclude.id).exists()
    return not query.exists()
