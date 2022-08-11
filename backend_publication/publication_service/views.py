import json
import uuid
import django_filters.rest_framework

from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.request import Request

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
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['user_uid', 'content_type', 'object_id']


class PublicationViewSet(viewsets.ModelViewSet):
    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer
    pagination_class = Pagination
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['author_uid', 'tags__name']


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    pagination_class = Pagination
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['publication']


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
