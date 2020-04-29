import pytest
from django.core.exceptions import ValidationError

pytestmark = pytest.mark.django_db()


class TestDateFrame:
    def test_create_task_event_with_valid_data(self, task_event_model, task_event_data, task_instance):
        task_event = task_event_model.objects.create(task=task_instance, **task_event_data)

        assert task_event is not None
        assert task_event.task == task_instance

    @pytest.mark.parametrize(
        'invalid_field_key, invalid_field_value, expected_exception',
        [
            ('start', '', ValidationError),
            ('task', None, ValidationError)
        ]
    )
    def test_create_task_event_with_invalid_data(self, invalid_field_key, invalid_field_value, expected_exception,
                                                 task_event_model, task_event_data, task_instance):
        task_event_data['task'] = task_instance
        task_event_data[invalid_field_key] = invalid_field_value

        with pytest.raises(expected_exception):
            task_event_model.objects.create(**task_event_data)

    @pytest.mark.parametrize(
        'data_corruption_cmd, expected_exception',
        [
            ("task_event_data['end'] = task_event_data['start']", ValidationError),
            ("task_event_data['end'], task_event_data['start']=task_event_data['start'],task_event_data['end']",
             ValidationError)
        ]
    )
    def test_create_task_event_with_corrupted_data(self, data_corruption_cmd, expected_exception, task_event_model,
                                                   task_event_data, task_instance):
        exec(data_corruption_cmd)

        with pytest.raises(expected_exception) as exc:
            task_event_model.objects.create(task=task_instance, **task_event_data)

        assert 'start' in exc.value.error_dict
