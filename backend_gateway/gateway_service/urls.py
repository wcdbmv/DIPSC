from django.urls import path

from .views import Users
from .views import tags, votes, publications, comments


urlpatterns = [
    path(r'users/', Users.as_view()),

    path(r'tags/', tags),
    path(r'votes/', votes),
    path(r'publications/', publications),
    path(r'comments/', comments),
]
