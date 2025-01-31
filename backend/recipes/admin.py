from django.contrib import admin # type: ignore

from .models import Tag, Ingredient, Recipe, IngredientInRecipe, CartItem, FavoriteItem


class IngredientInRecipeInline(admin.TabularInline):
    model = IngredientInRecipe
    min_num = 1  # Минимальное количество форм, которые должны быть заполнены
    verbose_name = 'Ингредиент'
    verbose_name_plural = 'Ингредиенты'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'slug'
    )
    list_editable = (
        'name',
        'slug'
    )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'measurement_unit'
    )
    list_editable = (
        'name',
        'measurement_unit'
    )
    search_fields = (
        'name',
    )


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'text',
        'image',
        'cooking_time',
        'author',
    )
    list_editable = (
        'name',
        'text',
        'image',
        'cooking_time',
        'author',
    )
    search_fields = (
        'author',
        'name'
    )
    list_filter = (
        'tags',
    )
    inlines = [IngredientInRecipeInline]