from rest_framework import pagination, viewsets

from .models import UuidUser
from .serializers import UuidUserSerializer


class UuidUserViewSet(viewsets.ModelViewSet):
    queryset = UuidUser.objects.all()
    serializer_class = UuidUserSerializer
    pagination_class = pagination.PageNumberPagination
