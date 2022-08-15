from django.urls import path

from .views import users, user_by_token
from .views import tags, votes, vote, Publications, Publication, comments, comment
from .views import subscriptions


urlpatterns = [
    path(r'users/', users),
    path(r'user-by-token/', user_by_token),

    path(r'tags/', tags),
    path(r'votes/', votes),
    path(r'vote/', vote),
    path(r'publications/', Publications.as_view()),
    path(r'publications/<uuid:uid>/', Publication.as_view()),
    path(r'comments/', comments),
    path(r'comments/<uuid:uid>/', comment),

    path(r'subscriptions/', subscriptions),
]
