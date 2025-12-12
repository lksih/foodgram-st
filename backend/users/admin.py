from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AvataredUser, Follow

admin.site.register(AvataredUser, UserAdmin)
admin.site.register(Follow, UserAdmin)
