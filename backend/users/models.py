from django.contrib.auth.models import AbstractUser
from django.db import models


class AvataredUser(AbstractUser):
    avatar = models.models.ImageField(
        'Аватар',
        upload_to='avatars/',
        default='avatars/default.jpg'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username
