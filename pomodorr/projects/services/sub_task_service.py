from pomodorr.projects.selectors.sub_task_selector import get_all_sub_tasks_for_task


def is_sub_task_name_available(task, name: str, excluded=None) -> bool:
    query = get_all_sub_tasks_for_task(task=task, name=name)
    if excluded is not None:
        return not query.exclude(id=excluded.id).exists()
    return not query.exists()
