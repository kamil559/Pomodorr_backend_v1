from datetime import datetime
from unittest.mock import patch

import pytest
from django.utils import timezone

from pomodorr.tools.utils import get_time_delta, get_default_domain


@patch('pomodorr.tools.utils.timezone')
def test_get_time_delta(mock_timezone):
    mock_timezone.now.return_value = datetime(2020, 1, 15, tzinfo=timezone.utc)

    utc_time_tomorrow = get_time_delta({'days': 1}, ahead=True)

    assert utc_time_tomorrow == datetime(2020, 1, 16, tzinfo=timezone.utc)


@patch('pomodorr.tools.utils.timezone')
def test_get_negative_time_delta(mock_timezone):
    mock_timezone.now.return_value = datetime(2020, 1, 15, tzinfo=timezone.utc)

    utc_time_tomorrow = get_time_delta({'days': 1}, ahead=False)

    assert utc_time_tomorrow == datetime(2020, 1, 14, tzinfo=timezone.utc)


@pytest.mark.django_db
def test_get_default_domain():
    default_domain = get_default_domain()

    assert default_domain is not None
