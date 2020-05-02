import pytest

pytestmark = pytest.mark.django_db


class TestDateFrame:
    def test_get_all_date_frames(self, date_frame_selector, date_frame_in_progress_for_yesterday,
                                 date_frame_create_batch, date_frame_for_random_task):
        selector_method_result = date_frame_selector.get_all_date_frames()

        assert selector_method_result.count() == 7
        assert date_frame_in_progress_for_yesterday in selector_method_result
        assert date_frame_for_random_task in selector_method_result
        assert all(date_frame in selector_method_result for date_frame in date_frame_create_batch)

    def test_get_all_date_frames_for_user(self):
        pass

    def test_get_all_date_frames_for_project(self):
        pass

    def test_get_all_date_frames_for_task(self):
        pass

    def test_get_breaks_inside_date_frame(self):
        pass

    def test_get_pauses_inside_date_frame(self):
        pass


class TestPomodoroSelector:
    def test_get_all_pomodoros(self):
        pass

    def test_get_finished_pomodoros(self):
        pass

    def test_get_unfinished_pomodoros(self):
        pass


class BreakSelector:
    def test_get_all_breaks(self):
        pass

    def test_get_finished_breaks(self):
        pass

    def test_get_unfinished_breaks(self):
        pass


class PauseSelector:
    def test_get_all_pauses(self):
        pass

    def test_get_finished_pauses(self):
        pass

    def test_get_unfinished_pauses(self):
        pass
