from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    external_id = models.IntegerField(
        verbose_name='Телеграм ID',
        unique=True,
        db_index=True,
        null=True,
    )


