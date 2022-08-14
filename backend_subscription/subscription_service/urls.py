from django.urls import include, path
from rest_framework import routers

from .views import SubscriptionViewSet


router = routers.DefaultRouter()
router.register(r'subscriptions', SubscriptionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
