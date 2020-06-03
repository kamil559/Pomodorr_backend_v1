from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from rest_framework import serializers

from pomodorr.tools.validators import image_size_validator
from pomodorr.user_settings.serializers import UserSettingSerializer

User = get_user_model()


class UserDetailSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False, validators=(
        image_size_validator,
        FileExtensionValidator(allowed_extensions=User.ALLOWED_AVATAR_EXTENSIONS)
    ))
    settings = UserSettingSerializer(many=False, required=False)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'avatar',
            'settings'
        )
        extra_kwargs = {
            'avatar': {
                'source': 'get_avatar_url'
            }
        }

    def create(self, validated_data):
        validated_data.pop('settings')
        return super(UserDetailSerializer, self).create(validated_data=validated_data)

    def update(self, instance, validated_data):
        settings_data = validated_data.pop('settings') or None

        if settings_data is not None:
            settings_object = instance.settings
            for field in settings_data.keys():
                setattr(settings_object, field, settings_data[field])
            settings_object.save()

        return super(UserDetailSerializer, self).update(instance=instance, validated_data=validated_data)
