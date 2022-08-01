import uuid

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Tag(models.Model):
    tag_uid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.SlugField(unique=True)


class Vote(models.Model):
    VALUES = (
        ('UP', 1),
        ('DOWN', -1),
    )
    value = models.SmallIntegerField(choices=VALUES)
    user_uid = models.UUIDField(default=uuid.uuid4, editable=False)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')


class Publication(models.Model):
    publication_uid = models.UUIDField(default=uuid.uuid4, editable=False)

    author_uid = models.UUIDField(default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    body = models.TextField()
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    tags = models.ManyToManyField(to=Tag, related_name='publications')

    rating = models.SmallIntegerField(default=0)
    votes = GenericRelation(Vote)


class Comment(models.Model):
    comment_uid = models.UUIDField(default=uuid.uuid4, editable=False)
    author_uid = models.UUIDField(default=uuid.uuid4, editable=False)
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
    body = models.TextField()
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    rating = models.SmallIntegerField(default=0)
    votes = GenericRelation(Vote)
