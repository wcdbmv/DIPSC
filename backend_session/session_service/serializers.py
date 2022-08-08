from rest_framework import serializers

from .models import UuidUser


class UuidUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UuidUser
        fields = ['id', 'last_login', 'is_superuser', 'username', 'first_name', 'last_name', 'email', 'is_staff',
                  'is_active', 'date_joined', 'groups', 'user_permissions']
