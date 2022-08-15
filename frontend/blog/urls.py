from django.urls import path

from .views import *


app_name = 'blog'
urlpatterns = [
    # ex: /blog/publications/
    path('publications/', publications_view, name='publications'),
    # ex: /blog/user/wcdbmv/
    path('user/<str:username>/', blog_view, name='user_publications'),
    # ex: /blog/feed/
    path('feed/', feed_view, name='feed'),
    # ex: /blog/publications/5/
    path('publications/<uuid:pk>/', publication_view, name='publication'),
    # ex: /blog/publications/5/upvote/
    path('publications/<uuid:pk>/upvote/', VoteView.as_view(content_type='publication', value=1), name='publication_upvote'),
    # ex: /blog/publications/5/downvote/
    path('publications/<uuid:pk>/downvote/', VoteView.as_view(content_type='publication', value=-1), name='publication_downvote'),
    # ex: /blog/publications/create/
    path('publications/create/', PublicationCreateView.as_view(), name='create_publication'),
    # ex: /blog/publications/5/update/
    path('publications/create/<uuid:pk>/update/', PublicationUpdateView.as_view(), name='update_publication'),
    # ex: /blog/publications/5/delete/
    path('publications/<uuid:pk>/delete/', PublicationDeleteView.as_view(), name='delete_publication'),
    # ex: /blog/publications/5/comment/
    path('publications/<uuid:pk>/comment/', CommentCreateView.as_view(), name='create_comment'),
    # ex: /blog/publications/5/update/
    path('comments/<uuid:pk>/update/', CommentUpdateView.as_view(), name='update_comment'),
    # ex: /blog/publications/5/delete/
    path('comments/<uuid:pk>/delete/', CommentDeleteView.as_view(), name='delete_comment'),
    # ex: /blog/tags/job/
    path('tags/<str:tag>/', tag_view, name='tag'),
    # ex: /blog/comments/15/upvote/
    path('comments/<uuid:pk>/upvote/', VoteView.as_view(content_type='comment', value=1), name='comment_upvote'),
    # ex: /blog/comments/15/downvote/
    path('comments/<uuid:pk>/downvote/', VoteView.as_view(content_type='comment', value=-1), name='comment_downvote'),
    #
    path('user/<str:obj_name>/subscribe/', Subscribe.as_view(obj='user', subscribe=True), name='subscribe_author'),
    #
    path('user/<str:obj_name>/unsubscribe/', Subscribe.as_view(obj='user', subscribe=False), name='unsubscribe_author'),
    #
    path('tag/<str:obj_name>/subscribe/', Subscribe.as_view(obj='tag', subscribe=True), name='subscribe_tag'),
    #
    path('tag/<str:obj_name>/unsubscribe/', Subscribe.as_view(obj='tag', subscribe=False), name='unsubscribe_tag'),
]
