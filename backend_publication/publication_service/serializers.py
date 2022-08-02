from rest_framework import serializers

from .models import Tag, Vote, Publication, Comment


class TagSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Tag
        fields = serializers.ALL_FIELDS


class VoteSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Vote
        fields = ['id', 'vote_uid', 'value', 'user_uid', 'content_object']


class PublicationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Publication
        fields = serializers.ALL_FIELDS


class CommentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Comment
        fields = serializers.ALL_FIELDS
