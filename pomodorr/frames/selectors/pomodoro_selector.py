from pomodorr.frames.models import Pomodoro


def get_all_pomodoros(**kwargs):
    return Pomodoro.objects.all(**kwargs)


def get_finished_pomodoros(**kwargs):
    return Pomodoro.objects.filter(start__isnull=False, end__isnull=False, **kwargs)


def get_unfinished_pomodoros(**kwargs):
    return Pomodoro.objects.filter(start__isnull=False, end__isnull=True, **kwargs)
