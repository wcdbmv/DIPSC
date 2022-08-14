from rest_framework import serializers

from .models import Subscription


class SubscriptionSerializer(serializers.ModelSerializer):
    follower_uid = serializers.UUIDField()
    following_uid = serializers.UUIDField()

    class Meta:
        model = Subscription
        fields = serializers.ALL_FIELDS
