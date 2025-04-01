from django.contrib.auth import get_user_model
from rest_framework import serializers

from currency.models import UserBalance

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")

    def create(self, validated_data):
        """Create User with encrypted password and initial balance"""
        user = User.objects.create_user(**validated_data)
        UserBalance.objects.create(user=user, balance=1000)
        return user

    def update(self, instance, validated_data):
        """Update User with encrypted password"""
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user
