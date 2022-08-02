from django.urls import include, path
from rest_framework import routers
from .views import TagViewSet, VoteViewSet, PublicationViewSet, CommentViewSet


router = routers.DefaultRouter()
router.register(r'tags', TagViewSet)
router.register(r'votes', VoteViewSet)
router.register(r'publications', PublicationViewSet)
router.register(r'comments', CommentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
