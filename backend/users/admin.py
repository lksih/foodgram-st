from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AvataredUser, Follow


class AvataredUserAdmin(UserAdmin):
    """Админка для модели пользователя."""

    list_display = ("username", "email", "first_name", "last_name")
    search_fields = ("email", "username")
    list_filter = ("is_staff", "is_superuser", "is_active")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Информация",
         {"fields": ("first_name", "last_name", "email", "avatar")}),
        (
            "Разрешения",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Даты активности", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {"fields": ("username", "password1", "password2")}),
        ("Информация",
         {"fields": ("first_name", "last_name", "email", "avatar")}),
        (
            "Разрешения",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )


class FollowAdmin(admin.ModelAdmin):
    """Админка для модели подписок."""

    list_display = ("user", "following")
    search_fields = (
        "user__username",
        "user__email",
        "following__username",
        "following__email",
    )
    list_filter = ("user", "following")


admin.site.register(AvataredUser, AvataredUserAdmin)
admin.site.register(Follow, FollowAdmin)
