from django.urls import path

from .views import *


app_name = 'blog'
urlpatterns = [
    # ex: /blog/feed/
    path('feed/', feed, name='feed'),
    # ex: /blog/user/wcdbmv
    # path('user/<str:username>', BlogView.as_view(), name='user_publications'),
    # ex: /blog/article/5/
    # path('article/<int:pk>/', ArticleView.as_view(), name='articles'),
    # ex: /blog/article/5/upvote
    # path('article/<int:pk>/upvote', VoteView.as_view(model=None, vote_value=1), name='article_upvote'),
    # ex: /blog/article/5/downvote
    # path('article/<int:pk>/downvote', VoteView.as_view(model=None, vote_value=-1), name='article_downvote'),
    # ex: /blog/article/create/
    # path('article/create/', ArticleCreate.as_view(), name='create_article'),
    # ex: /blog/article/5/update
    # path('article/create/<int:pk>/update', ArticleUpdate.as_view(), name='update_article'),
    # ex: /blog/article/5/delete
    # path('article/<int:pk>/delete', ArticleDelete.as_view(), name='delete_article'),
    # ex: /blog/article/5/comment/
    # path('article/<int:pk>/comment/', CommentCreate.as_view(), name='create_comment'),
    # ex: /blog/article/5/update
    # path('comment/<int:pk>/update', CommentUpdate.as_view(), name='update_comment'),
    # ex: /blog/article/5/delete
    # path('comment/<int:pk>/delete', CommentDelete.as_view(), name='delete_comment'),
    # ex: /blog/tag/job
    # path('tag/<str:tag>/', TagView.as_view(), name='tag'),
    # ex: /blog/comment/15/upvote
    # path('comment/<int:pk>/upvote', VoteView.as_view(model=Comment, vote_value=1), name='article_upvote'),
    # ex: /blog/comment/15/downvote
    # path('comment/<int:pk>/downvote', VoteView.as_view(model=Comment, vote_value=-1), name='article_downvote'),
]
