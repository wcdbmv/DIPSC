from django.urls import include, path
from rest_framework import routers

from .views import StatisticsViewSet


router = routers.DefaultRouter()
router.register(r'statistics', StatisticsViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
