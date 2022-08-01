from django.contrib import admin

from .models import Tag, Vote, Publication, Comment


admin.site.register(Tag)
admin.site.register(Vote)
admin.site.register(Publication)
admin.site.register(Comment)
