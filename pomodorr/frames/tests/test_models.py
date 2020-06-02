import pytest
from django.core.exceptions import ValidationError

from pomodorr.frames.exceptions import DateFrameException

pytestmark = pytest.mark.django_db()


class TestDateFrame:
    def test_create_date_frame_with_valid_data(self, date_frame_model, date_frame_data, task_instance):
        date_frame = date_frame_model.objects.create(task=task_instance, **date_frame_data)

        assert date_frame is not None
        assert date_frame.task == task_instance

    @pytest.mark.parametrize(
        'invalid_field_key, invalid_field_value, expected_exception',
        [
            ('frame_type', None, ValidationError),
            ('frame_type', '', ValidationError),
            ('frame_type', '3', ValidationError),
            ('start', '', ValidationError),
            ('task', None, ValidationError)
        ]
    )
    def test_create_date_frame_with_invalid_data(self, invalid_field_key, invalid_field_value, expected_exception,
                                                 date_frame_model, date_frame_data, task_instance):
        date_frame_data['task'] = task_instance
        date_frame_data[invalid_field_key] = invalid_field_value

        with pytest.raises(expected_exception):
            date_frame_model.objects.create(**date_frame_data)

    def test_create_date_frame_with_start_greater_than_end(self, date_frame_model, date_frame_data, task_instance):
        with pytest.raises(ValidationError) as exc:
            date_frame_data['start'], date_frame_data['end'] = date_frame_data['end'], date_frame_data['start']

            date_frame_model.objects.create(task=task_instance, **date_frame_data)

        assert exc.value.messages[0] == DateFrameException.messages[DateFrameException.start_greater_than_end]

    def test_create_date_frame_for_completed_task(self, date_frame_model, date_frame_data, completed_task_instance):
        with pytest.raises(ValidationError) as exc:
            date_frame_model.objects.create(task=completed_task_instance, **date_frame_data)

        assert exc.value.messages[0] == DateFrameException.messages[DateFrameException.task_already_completed]
