from django.contrib import admin
from django.db.models import Count

from .models import Ingredient, Recipe, Tag


class RecipeIngredientsInLine(admin.TabularInline):
    model = Recipe.ingredients.through
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
        'name',
        'image',
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

    inlines = (RecipeIngredientsInLine, )

    def get_queryset(self, request):
        queryset = super().get_queryset(request) 
        return queryset.annotate(favorites_count=Count('favorite_items'))

    def count_favorites(self, obj: Recipe):
        return obj.favorites_count

    count_favorites.short_description = "В избранном"
    count_favorites.admin_order_field = 'favorites_count'
