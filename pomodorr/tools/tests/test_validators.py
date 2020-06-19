from datetime import timedelta
from unittest.mock import Mock

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError

from pomodorr.tools.utils import get_time_delta
from pomodorr.tools.validators import image_size_validator, duration_validator, today_validator


class TestImageSizeValidator:
    @pytest.mark.parametrize(
        'tested_size',
        [
            0,
            settings.MAX_UPLOAD_SIZE - 1,
            settings.MAX_UPLOAD_SIZE
        ]
    )
    def test_validate_image_with_valid_sizes(self, tested_size):
        file = Mock
        file.size = tested_size

        image_size_validator(file_object=file)

    @pytest.mark.parametrize(
        'tested_size',
        [
            settings.MAX_UPLOAD_SIZE + 1,
            settings.MAX_UPLOAD_SIZE + 5000
        ]
    )
    def test_validate_image_with_exceeding_sizes(self, tested_size):
        file = Mock
        file.size = tested_size

        with pytest.raises(ValidationError):
            image_size_validator(file_object=file)


class TestDurationValidation:
    @pytest.mark.parametrize(
        'tested_duration',
        [
            timedelta(hours=24),
            timedelta(days=1),
            timedelta(days=2, minutes=0),
            timedelta(days=365),
            timedelta(weeks=1),
            timedelta(weeks=10),
        ]
    )
    def test_validate_duration_with_valid_durations(self, tested_duration):
        duration_validator(value=tested_duration)

    @pytest.mark.parametrize(
        'tested_duration',
        [
            timedelta(seconds=1),
            timedelta(minutes=1),
            timedelta(minutes=55),
            timedelta(minutes=55, seconds=51),
            timedelta(hours=24, minutes=10),
            timedelta(days=1, minutes=5),
            timedelta(days=365, milliseconds=1),
            timedelta(weeks=1, minutes=1),
            timedelta(weeks=10, days=5, hours=23, minutes=4),
        ]
    )
    def test_validate_duration_with_invalid_durations(self, tested_duration):
        with pytest.raises(ValidationError):
            duration_validator(value=tested_duration)


class TestTodayValidator:

    @pytest.mark.parametrize(
        'tested_date',
        [
            get_time_delta({'days': 0}),
            get_time_delta({'days': 1}),
            get_time_delta({'days': 5}),
        ]
    )
    def test_validate_today_with_valid_dates(self, tested_date):
        today_validator(value=tested_date)

    @pytest.mark.parametrize(
        'tested_date',
        [
            get_time_delta({'days': 1}, ahead=False),
            get_time_delta({'days': 5}, ahead=False),
        ]
    )
    def test_validate_today_with_invalid_dates(self, tested_date):
        with pytest.raises(ValidationError):
            today_validator(value=tested_date)
