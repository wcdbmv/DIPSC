from django.urls import include, path
from rest_framework import routers

from .views import UuidUserViewSet
from .views import user_by_token


router = routers.DefaultRouter()
router.register(r'users', UuidUserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('user-by-token/', user_by_token),
]
