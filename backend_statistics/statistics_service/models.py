import uuid

from django.db import models


class Statistics(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    publication_uid = models.UUIDField()
    viewer_uid = models.UUIDField(blank=True, null=True)

    view_date = models.DateTimeField('date viewed', auto_now_add=True)
