from django.contrib import admin
from django.db.models import Count
from .models import Ingredient, Recipe, Tag


class RecipeIngredientsInLine(admin.TabularInline):
    model = Recipe.ingredients.through
    extra = 1


class RecipeTagsInLine(admin.TabularInline):
    model = Recipe.tags.through
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'slug'
    )
    search_fields = (
        'name',
    )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'measurement_unit'
    )
    search_fields = (
        'name',
    )
    ordering = ('id',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'text',
        'image',
        'cooking_time',
        'author',
        'count_favorites'
    )
    list_editable = (
        'name',
        'text',
        'image',
        'cooking_time',
        'author',
    )
    search_fields = (
        'name',
        'author__username',
    )
    list_filter = (
        'tags',
    )
    inlines = (RecipeIngredientsInLine, RecipeTagsInLine)

    def get_queryset(self, request):
        """
        Добавляем аннотацию для подсчета избранных рецептов.
        """
        queryset = super().get_queryset(request)
        return queryset.annotate(favorites_count=Count('in_favorites'))

    def count_favorites(self, obj: Recipe) -> int:
        """
        Возвращает количество добавлений рецепта в избранное.
        """
        return obj.favorites_count

    count_favorites.short_description = "В избранном"
    count_favorites.admin_order_field = 'favorites_count'
