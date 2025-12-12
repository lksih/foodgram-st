from django.contrib.auth.models import AbstractUser
from django.db import models


class AvataredUser(AbstractUser):
    avatar = models.ImageField(
        'Аватар',
        upload_to='avatars/',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(
        AvataredUser, on_delete=models.CASCADE, related_name='follows')
    following = models.ForeignKey(
        AvataredUser, on_delete=models.CASCADE, related_name='followers')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} подписан на {self.following}'
