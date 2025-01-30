from django.db import models
from django.contrib.auth.models import AbstractUser

MAX_LENGTH_FIELD = 150


class User(AbstractUser):
    email = models.EmailField(
        "Почта",
        max_length=MAX_LENGTH_FIELD,
        unique=True
    )
    username = models.CharField(
        "Имя пользователя",
        max_length=MAX_LENGTH_FIELD,
        unique=True,
    )

    first_name = models.CharField(
        'Имя',
        max_length=MAX_LENGTH_FIELD,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=MAX_LENGTH_FIELD,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name',]

    class Meta():
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username
