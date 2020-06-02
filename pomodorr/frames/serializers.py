from rest_framework.serializers import ModelSerializer

from pomodorr.frames.models import DateFrame


class DateFrameSerializer(ModelSerializer):
    class Meta:
        model = DateFrame
        fields = ('id', 'created', 'modified', 'start', 'end', 'duration', 'frame_type')

    def to_representation(self, instance):
        data = super(DateFrameSerializer, self).to_representation(instance=instance)
        data['frame_type'] = instance.get_frame_type_display()
        return data
