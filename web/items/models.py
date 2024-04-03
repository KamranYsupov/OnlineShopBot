from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.db import models


class Category(models.Model):
    name = models.CharField(verbose_name='Название категории', max_length=25, )
    parent_category = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='subcategories',
        blank=True,
        null=True,
        verbose_name='Родительский категория',
    )

    def __str__(self):
        return self.name


class Item(models.Model):
    name = models.CharField(verbose_name='Название продукта', max_length=25, )
    price = models.FloatField(verbose_name='Цена')
    description = models.TextField(
        verbose_name='Описание продукта',
        max_length=500,
        blank=True)
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='items/images/',
        validators=[FileExtensionValidator(
            allowed_extensions=['jpg', 'jpeg', 'png', 'svg']
        )], blank=True, null=True, )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT
        , related_name='items',
        verbose_name='Категория'
    )

    def __str__(self):
        return f'{self.name} - {self.price}'


class Basket(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='basket')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='basket')
    quantity = models.PositiveIntegerField(verbose_name='Количество')


