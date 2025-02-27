from django.contrib import admin
from django.db.models import Count

from .models import Ingredient, Recipe, Tag


class RecipeIngredientsInLine(admin.TabularInline):
    model = Recipe.ingredients.through
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'slug',
        'name',
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
    list_display_links = (
        'id',
        'name',
    )
    search_fields = (
        'name',
    )
    ordering = ('id',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'text',
        'author',
        'cooking_time',
        'count_favorites',
        'image',
    )
    search_fields = (
        'name',
    )
    list_filter = (
        'tags',
        'author__username',

    )

    inlines = (RecipeIngredientsInLine, )

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related(
            'author'
        ).prefetch_related(
            'ingredients', 'tags'
        ).annotate(
            favorites_count=Count('favoriteitem_items')
        )
        return queryset

    def count_favorites(self, obj: Recipe):
        return obj.favorites_count

    count_favorites.short_description = 'В избранном'
    count_favorites.admin_order_field = 'favorites_count'
