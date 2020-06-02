import pytest

from pomodorr.frames.serializers import DateFrameSerializer

pytestmark = pytest.mark.django_db


class TestDateFrameSerializer:
    serializer_class = DateFrameSerializer

    def test_serializer_returns_proper_frame_type(self, date_frame_model, date_frame_create_batch):
        serializer = self.serializer_class(instance=date_frame_model.objects.all(), many=True)

        assert serializer.data is not None
        assert type(serializer.data[0]['frame_type']) == str
