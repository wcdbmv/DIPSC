from django.urls import include, path
from rest_framework import routers
from .views import TagViewSet, TagUidViewSet, VoteViewSet, PublicationViewSet, CommentViewSet, content_types, vote


router = routers.DefaultRouter()
router.register(r'tags_uid', TagUidViewSet)
router.register(r'tags', TagViewSet)
router.register(r'votes', VoteViewSet)
router.register(r'publications', PublicationViewSet, basename='Publication')
router.register(r'comments', CommentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('content-types/', content_types),
    path('vote/', vote),
]
