from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from rest_framework import serializers
from pomodorr.tools.validators import validate_image

User = get_user_model()


class UserDetailSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False, validators=(
        validate_image,
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
