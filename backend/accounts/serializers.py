
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field, inline_serializer

from .models import Profile


class ProfileSerializer(serializers.Serializer):
    """Преобразование профиля в формат Swagger."""

    fullName = serializers.CharField(source="user.first_name")
    email = serializers.EmailField(source="user.email")
    phone = serializers.CharField()
    avatar = serializers.SerializerMethodField()

    @extend_schema_field(
        inline_serializer(
            name="ProfileAvatar",
            fields={
                "src": serializers.CharField(),
                "alt": serializers.CharField(),
            },
        )
    )
    def get_avatar(self, obj):
        if not obj.avatar:
            return {
                "src": "",
                "alt": "Аватар пользователя",
            }

        return {
            "src": obj.avatar.url,
            "alt": f"Аватар {obj.user.username}",
        }
