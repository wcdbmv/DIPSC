from django.urls import include, path
from rest_framework import routers
from .views import UuidUserViewSet


router = routers.DefaultRouter()
router.register(r'users', UuidUserViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
