from rest_framework import serializers

from .models import Tag, Vote, Publication, Comment


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = serializers.ALL_FIELDS


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = serializers.ALL_FIELDS


class PublicationSerializer(serializers.ModelSerializer):
    tags = serializers.SlugRelatedField(slug_field='name', many=True, read_only=True)

    class Meta:
        model = Publication
        fields = serializers.ALL_FIELDS


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = serializers.ALL_FIELDS
