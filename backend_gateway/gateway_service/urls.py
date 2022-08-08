from django.urls import path

from .views import Users, user_by_token
from .views import tags, votes, publications, comments


urlpatterns = [
    path(r'users/', Users.as_view()),
    path(r'user-by-token/', user_by_token),

    path(r'tags/', tags),
    path(r'votes/', votes),
    path(r'publications/', publications),
    path(r'comments/', comments),
]
