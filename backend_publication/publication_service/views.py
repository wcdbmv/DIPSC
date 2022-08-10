import django_filters.rest_framework
from rest_framework import viewsets

from .models import Tag, Vote, Publication, Comment
from .pagination import Pagination
from .serializers import TagSerializer, VoteSerializer, PublicationSerializer, CommentSerializer


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = Pagination
    lookup_field = 'name'


class VoteViewSet(viewsets.ModelViewSet):
    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    pagination_class = Pagination


class PublicationViewSet(viewsets.ModelViewSet):
    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer
    pagination_class = Pagination
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['author_uid']


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    pagination_class = Pagination
