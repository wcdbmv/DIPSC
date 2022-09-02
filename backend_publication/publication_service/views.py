import json
import uuid
import django_filters.rest_framework

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponse
from rest_framework import filters, status, viewsets

from rest_framework.decorators import api_view
from rest_framework.request import Request

from .models import Tag, Vote, Publication, Comment
from .pagination import Pagination
from .serializers import TagSerializer, VoteSerializer, PublicationSerializer, CommentSerializer


class TagUidViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = Pagination


class TagViewSet(TagUidViewSet):
    lookup_field = 'name'


class VoteViewSet(viewsets.ModelViewSet):
    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    pagination_class = Pagination
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['user_uid', 'content_type', 'object_id']


class PublicationViewSet(viewsets.ModelViewSet):
    serializer_class = PublicationSerializer
    pagination_class = Pagination
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['author_uid', 'tags__name']
    ordering_fields = ['pub_date', 'rating']
    ordering = ['-pub_date']
    search_fields = ['title', 'body']

    def get_queryset(self):
        queryset = Publication.objects.all()
        authors = self.request.query_params.get('author_uid__in')
        tag_names = self.request.query_params.get('tags__name__in')
        tag_ids = self.request.query_params.get('tags__id__in')

        if authors:
            if tag_names:
                return queryset.filter(Q(author_uid__in=authors.split(',')) | Q(tags__name__in=tag_names.split(',')))
            if tag_ids:
                return queryset.filter(Q(author_uid__in=authors.split(',')) | Q(tags__id__in=tag_ids.split(',')))
            return queryset.filter(author_uid__in=authors.split(','))
        if tag_names:
            return queryset.filter(tags__name__in=tag_names.split(','))
        if tag_ids:
            return queryset.filter(tags__id__in=tag_ids.split(','))
        if authors is not None and tag_ids is not None:
            return Publication.objects.none()
        return queryset


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    pagination_class = Pagination
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['publication']
    ordering_fields = ['pub_date', 'rating']


@api_view(['GET'])
def content_types(request: Request) -> HttpResponse:
    return HttpResponse(content=json.dumps({
        'publication': ContentType.objects.get_for_model(Publication).id,
        'comment': ContentType.objects.get_for_model(Comment).id,
    }), content_type='application/json')


@api_view(['POST'])
def vote(request: Request) -> HttpResponse:
    match request.data['content_type']:
        case 'publication':
            model = Publication
        case 'comment':
            model = Comment
        case _:
            return HttpResponse(content=b'Unsupported content_type', status=status.HTTP_400_BAD_REQUEST,
                                content_type='application/json')

    user_uid = uuid.UUID(request.data['user_uid'])
    object_id = uuid.UUID(request.data['object_id'])
    vote_value = int(request.data['value'])

    obj = model.objects.get(id=object_id)
    content_type = ContentType.objects.get_for_model(obj)
    try:
        vote_obj = Vote.objects.get(user_uid=user_uid, content_type=content_type, object_id=obj.id)
        if vote_obj.value is not vote_value:
            vote_obj.value = vote_value
            vote_obj.save(update_fields=['value'])
            obj.rating += 2 * vote_value
            obj.save(update_fields=['rating'])
        else:
            obj.rating -= vote_obj.value
            obj.save(update_fields=['rating'])
            vote_obj.delete()
    except Vote.DoesNotExist:
        obj.votes.create(user_uid=user_uid, value=vote_value, content_type=content_type, object_id=obj.id)
        obj.rating += vote_value
        obj.save(update_fields=['rating'])

    return HttpResponse(json.dumps({'rating': obj.rating}), content_type='application/json')
