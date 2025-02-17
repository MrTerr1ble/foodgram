from io import BytesIO

from django.db.models import Sum

from recipes.models import CartItem, IngredientInRecipe


def generate_shopping_list(user):
    cart_items = CartItem.objects.filter(
        user=user
    ).values_list(
        'recipe', flat=True
    )
    ingredients_summary = (
        IngredientInRecipe.objects
        .filter(recipe__in=cart_items)
        .values('ingredient__name', 'ingredient__measurement_unit')
        .annotate(total_amount=Sum('amount'))
        .order_by('ingredient__name')
    )
    shopping_list_text = "Список покупок:\n\n"
    for item in ingredients_summary:
        ingredient_name = item['ingredient__name']
        total_amount = item['total_amount']
        unit = item['ingredient__measurement_unit']
        shopping_list_text += (
            f'{ingredient_name} — {total_amount} {unit}\n'
        )

    buffer = BytesIO()
    buffer.write(shopping_list_text.encode('utf-8'))
    buffer.seek(0)
    return buffer
