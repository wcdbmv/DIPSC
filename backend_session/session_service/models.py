import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


# Using a custom user model when starting a project
# https://docs.djangoproject.com/en/4.1/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project

class UuidUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
