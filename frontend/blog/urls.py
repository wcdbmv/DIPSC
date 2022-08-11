from django.urls import path

from .views import *


app_name = 'blog'
urlpatterns = [
    # ex: /blog/feed/
    path('feed/', feed_view, name='feed'),
    # ex: /blog/user/wcdbmv
    path('user/<str:username>', blog_view, name='user_publications'),
    # ex: /blog/publication/5/
    path('publication/<uuid:pk>/', publication_view, name='publications'),
    # ex: /blog/publication/5/upvote
    path('publication/<uuid:pk>/upvote', VoteView.as_view(content_type='publication', value=1), name='publication_upvote'),
    # ex: /blog/publication/5/downvote
    path('publication/<uuid:pk>/downvote', VoteView.as_view(content_type='publication', value=-1), name='publication_downvote'),
    # ex: /blog/publication/create/
    path('publication/create/', publication_create_view, name='create_publication'),
    # ex: /blog/publication/5/update
    path('publication/create/<uuid:pk>/update', publication_update_view, name='update_publication'),
    # ex: /blog/publication/5/delete
    path('publication/<uuid:pk>/delete', publication_delete_view, name='delete_publication'),
    # ex: /blog/publication/5/comment/
    path('publication/<uuid:pk>/comment/', comment_create_view, name='create_comment'),
    # ex: /blog/publication/5/update
    path('comment/<uuid:pk>/update', comment_update_view, name='update_comment'),
    # ex: /blog/publication/5/delete
    path('comment/<uuid:pk>/delete', comment_delete_view, name='delete_comment'),
    # ex: /blog/tag/job
    path('tag/<str:tag>/', tag_view, name='tag'),
    # ex: /blog/comment/15/upvote
    path('comment/<uuid:pk>/upvote', VoteView.as_view(content_type='comment', value=1), name='comment_upvote'),
    # ex: /blog/comment/15/downvote
    path('comment/<uuid:pk>/downvote', VoteView.as_view(content_type='comment', value=-1), name='comment_downvote'),
]
