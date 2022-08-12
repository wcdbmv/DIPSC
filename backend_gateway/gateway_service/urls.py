from django.urls import path

from .views import Users, user_by_token
from .views import tags, votes, vote, Publications, publication, Comments, Comment


urlpatterns = [
    path(r'users/', Users.as_view()),
    path(r'user-by-token/', user_by_token),

    path(r'tags/', tags),
    path(r'votes/', votes),
    path(r'vote/', vote),
    path(r'publications/', Publications.as_view()),
    path(r'publications/<uuid:uid>/', publication),
    path(r'comments/', Comments.as_view()),
    path(r'comments/<uuid:uid>/', Comment.as_view()),
]
