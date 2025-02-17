from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)
from django.db import models

from users.models import User


class Tag(models.Model):
    name = models.CharField(
        max_length=32,
        verbose_name='Название тега'
    )
    slug = models.CharField(
        max_length=32,
        verbose_name='Название slug',
        validators=[RegexValidator(
            regex=r'^[-a-zA-Z0-9_]+$',
            message='Введен некорекнтый логин.'
        ), ],
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=128,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=64,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f"{self.name}-({self.measurement_unit})"


class Recipe(models.Model):
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
    )
    author = models.ForeignKey(
        User,
        related_name='recipes',
        verbose_name='Автор',
        on_delete=models.CASCADE,
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        verbose_name='Ингредиент'
    )
    name = models.CharField(
        max_length=256,
        verbose_name='Название'
    )
    text = models.TextField(
        verbose_name='Текстовое описание'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления в минутах',
        validators=[
            MinValueValidator(1),
            MaxValueValidator(2000)
        ]
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='media/recipes/',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_list',
        verbose_name='Ингредиенты'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_recipe'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10000)
        ]
    )


class AbstractItem(models.Model):
    user = models.ForeignKey(
        User,
        related_name='%(class)s_items',
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='%(class)s_items',
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        unique_together = ('user', 'recipe')
        abstract = True


class CartItem(AbstractItem):
    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class FavoriteItem(AbstractItem):
    class Meta:
        verbose_name = 'Избранный товар'
        verbose_name_plural = 'Избранные товары'

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'
