from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from rest_framework import serializers

from pomodorr.tools.validators import image_size_validator

User = get_user_model()


class UserDetailSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False, validators=(
        image_size_validator,
        FileExtensionValidator(allowed_extensions=User.ALLOWED_AVATAR_EXTENSIONS)
    ))

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "avatar"
        )
        extra_kwargs = {"avatar": {"source": "get_avatar_url"}}
