import django_filters.rest_framework
from rest_framework import pagination, viewsets
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from .models import UuidUser
from .serializers import UuidUserSerializer


class UuidUserViewSet(viewsets.ModelViewSet):
    queryset = UuidUser.objects.all()
    serializer_class = UuidUserSerializer
    pagination_class = pagination.PageNumberPagination
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['username']


@api_view(['POST'])
def user_by_token(request: Request) -> Response:
    access_token_str = request.data['token']
    access_token_obj = AccessToken(access_token_str)
    user_id = access_token_obj['user_id']
    user = UuidUser.objects.get(id=user_id)
    return Response(UuidUserSerializer(user).data)
