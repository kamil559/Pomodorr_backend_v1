from pomodorr.frames.models import Pause


def get_all_pauses(**kwargs):
    return Pause.objects.all(**kwargs)


def get_finished_pauses(**kwargs):
    return Pause.objects.filter(start__isnull=False, end__isnull=False, **kwargs)


def get_unfinished_pauses(**kwargs):
    return Pause.objects.filter(start__isnull=False, end__isnull=True, **kwargs)
