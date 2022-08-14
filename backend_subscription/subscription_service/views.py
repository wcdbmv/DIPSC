import django_filters.rest_framework

from rest_framework import filters, viewsets

from .models import Subscription
from .pagination import Pagination
from .serializers import SubscriptionSerializer


class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    pagination_class = Pagination
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['follower_uid', 'following_uid']
    ordering = ['-sub_date']
