from rest_framework import serializers

from pomodorr.user_settings.models import UserSetting


class UserSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSetting
        fields = (
            'pomodoro_length',
            'short_break_length',
            'long_break_length',
            'long_break_after',
            'auto_pomodoro_start',
            'auto_break_start',
            'disable_breaks',
        )
