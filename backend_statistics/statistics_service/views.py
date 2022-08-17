import django_filters.rest_framework

from rest_framework import filters, viewsets

from .models import Statistics
from .pagination import Pagination
from .serializers import StatisticsSerializer


class StatisticsViewSet(viewsets.ModelViewSet):
    queryset = Statistics.objects.all()
    serializer_class = StatisticsSerializer
    pagination_class = Pagination
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['publication_uid']
    ordering = ['-view_date']
