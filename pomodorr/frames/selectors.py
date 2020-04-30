from pomodorr.frames.models import DateFrame, Pause, Pomodoro, Break


class DateFrameSelector:
    model = DateFrame

    @classmethod
    def get_all_date_frames(cls, **kwargs):
        return cls.model.objects.all(**kwargs)

    @classmethod
    def get_all_date_frames_for_user(cls, user, **kwargs):
        return cls.model.objects.filter(task__project__user=user, **kwargs)

    @classmethod
    def get_all_date_frames_for_project(cls, project, **kwargs):
        return cls.model.objects.filter(task__project=project, **kwargs)

    @classmethod
    def get_all_date_frames_for_task(cls, task, **kwargs):
        return cls.model.objects.filter(task=task, **kwargs)

    @classmethod
    def get_breaks_inside_date_frame(cls, date_frame_object, end=None):
        end = end if end is not None else date_frame_object.end

        if end is None:
            return

        return cls.model.objects.filter(start__gte=date_frame_object.start, end__lte=end, type=cls.model.break_type)

    @classmethod
    def get_pauses_inside_date_frame(cls, date_frame_object, end=None):
        end = end if end is not None else date_frame_object.end

        if end is None:
            return

        return cls.model.objects.filter(start__gte=date_frame_object.start, end__lte=end, type=cls.model.break_type)

    @classmethod
    def get_active_date_frames_for_task(cls, task, **kwargs):
        return cls.model.objects.filter(task=task, start__isnull=False, end__isnull=True, **kwargs)


class PomodoroSelector:
    model = Pomodoro

    @classmethod
    def get_all_pomodoros(cls, **kwargs):
        return cls.model.objects.all(**kwargs)

    @classmethod
    def get_finished_pomodoros(cls, **kwargs):
        return cls.model.objects.filter(start__isnull=False, end__isnull=False, **kwargs)

    @classmethod
    def get_unfinished_pomodoros(cls, **kwargs):
        return cls.model.objects.filter(start__isnull=False, end__isnull=True, **kwargs)


class BreakSelector:
    model = Break

    @classmethod
    def get_all_breaks(cls, **kwargs):
        return cls.model.objects.all(**kwargs)

    @classmethod
    def get_finished_breaks(cls, **kwargs):
        return cls.model.objects.filter(start__isnull=False, end__isnull=False, **kwargs)

    @classmethod
    def get_unfinished_breaks(cls, **kwargs):
        return cls.model.objects.filter(start__isnull=False, end__isnull=True, **kwargs)


class PauseSelector:
    model = Pause

    @classmethod
    def get_all_pauses(cls, **kwargs):
        return cls.model.objects.all(**kwargs)

    @classmethod
    def get_finished_pauses(cls, **kwargs):
        return cls.model.objects.filter(start__isnull=False, end__isnull=False, **kwargs)

    @classmethod
    def get_unfinished_pauses(cls, **kwargs):
        return cls.model.objects.filter(start__isnull=False, end__isnull=True, **kwargs)
