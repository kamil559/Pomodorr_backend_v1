class DateFrameSelector:
    def __init__(self, model_class):
        self.date_frame_model = model_class

    def get_all_date_frames(self, **kwargs):
        return self.date_frame_model.objects.all(**kwargs)

    def get_all_date_frames_for_user(self, user, **kwargs):
        return self.date_frame_model.objects.filter(task__project__user=user, **kwargs)

    def get_all_date_frames_for_project(self, project, **kwargs):
        return self.date_frame_model.objects.filter(task__project=project, **kwargs)

    def get_all_date_frames_for_task(self, task, **kwargs):
        return self.date_frame_model.objects.filter(task=task, **kwargs)

    def get_breaks_inside_date_frame(self, date_frame_object, end=None):
        end = end if end is not None else date_frame_object.end

        if end is None:
            return

        return self.date_frame_model.objects.filter(start__gte=date_frame_object.start, end__lte=end,
                                                    frame_type=self.date_frame_model.break_type)

    def get_pauses_inside_date_frame(self, date_frame_object, end=None):
        end = end if end is not None else date_frame_object.end

        if end is None:
            return

        return self.date_frame_model.objects.filter(start__gte=date_frame_object.start, end__lte=end,
                                                    frame_type=self.date_frame_model.pause_type)

    def get_active_date_frames_for_task(self, task, **kwargs):
        return self.date_frame_model.objects.filter(task=task, start__isnull=False, end__isnull=True, **kwargs)


class PomodoroSelector:
    def __init__(self, model_class):
        self.date_frame_model = model_class

    def get_all_pomodoros(self, **kwargs):
        return self.date_frame_model.objects.all(**kwargs)

    def get_finished_pomodoros(self, **kwargs):
        return self.date_frame_model.objects.filter(start__isnull=False, end__isnull=False, **kwargs)

    def get_unfinished_pomodoros(self, **kwargs):
        return self.date_frame_model.objects.filter(start__isnull=False, end__isnull=True, **kwargs)


class BreakSelector:
    def __init__(self, model_class):
        self.date_frame_model = model_class

    def get_all_breaks(self, **kwargs):
        return self.date_frame_model.objects.all(**kwargs)

    def get_finished_breaks(self, **kwargs):
        return self.date_frame_model.objects.filter(start__isnull=False, end__isnull=False, **kwargs)

    def get_unfinished_breaks(self, **kwargs):
        return self.date_frame_model.objects.filter(start__isnull=False, end__isnull=True, **kwargs)


class PauseSelector:
    def __init__(self, model_class):
        self.date_frame_model = model_class

    def get_all_pauses(self, **kwargs):
        return self.date_frame_model.objects.all(**kwargs)

    def get_finished_pauses(self, **kwargs):
        return self.date_frame_model.objects.filter(start__isnull=False, end__isnull=False, **kwargs)

    def get_unfinished_pauses(self, **kwargs):
        return self.date_frame_model.objects.filter(start__isnull=False, end__isnull=True, **kwargs)
