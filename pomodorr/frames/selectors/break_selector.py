from pomodorr.frames.models import Break


def get_all_breaks(**kwargs):
    return Break.objects.all(**kwargs)


def get_finished_breaks(**kwargs):
    return Break.objects.filter(start__isnull=False, end__isnull=False, **kwargs)


def get_unfinished_breaks(**kwargs):
    return Break.objects.filter(start__isnull=False, end__isnull=True, **kwargs)
