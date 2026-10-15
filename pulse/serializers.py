
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import PriceAlert, UserProfile

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(
            password=password,
            **validated_data,
        )


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["role", "created_at"]
        read_only_fields = ["role", "created_at"]


class PriceAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceAlert
        fields = [
            "id",
            "origin",
            "destination",
            "threshold_price",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]
