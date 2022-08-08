from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import UuidUser


admin.site.register(UuidUser, UserAdmin)
