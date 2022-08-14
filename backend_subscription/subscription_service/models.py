import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class Subscription(models.Model):
    subscription_uid = models.UUIDField(default=uuid.uuid4, editable=False)

    class Type(models.TextChoices):
        USER = 'user', _('user')
        TAG = 'tag', _('tag')

    type = models.CharField(max_length=4, choices=Type.choices)
    follower_uid = models.UUIDField(editable=False)
    following_uid = models.UUIDField(editable=False)

    sub_date = models.DateTimeField('date subscribed', auto_now_add=True)
