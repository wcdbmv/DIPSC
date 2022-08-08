from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from .models import UuidUser


class UuidUserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = UuidUser
        fields = ['id', 'password', 'username', 'first_name', 'last_name', 'email']

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data.get('password'))
        return super().create(validated_data)
