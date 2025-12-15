from django.contrib.auth.models import AbstractUser
from django.db import models


class AvataredUser(AbstractUser):
    email = models.EmailField(
        unique=True, blank=False, null=False, verbose_name="Электронная почта"
    )
    first_name = models.CharField("Имя", max_length=150)
    last_name = models.CharField("Фамилия", max_length=150)
    avatar = models.ImageField(
        "Аватар", upload_to="media/avatars/", blank=True, null=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(
        AvataredUser,
        on_delete=models.CASCADE,
        related_name="follows",
        verbose_name="Пользователь",
    )
    following = models.ForeignKey(
        AvataredUser,
        on_delete=models.CASCADE,
        related_name="followers",
        verbose_name="На кого подписан",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

    def __str__(self):
        return f"{self.user} подписан на {self.following}"
