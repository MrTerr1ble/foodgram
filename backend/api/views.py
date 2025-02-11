from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from api.pagination import CustomLimitPagination
from api.serializers import (
    AvatarSerializer,
    CustomUserSerializer,
    FavoriteRecipeSerializer,
    IngredientSerializer,
    ReadRecipeSerializer,
    SubscribeSerializer,
    TagSerializer,
    WriteRecipeSerializer,
)
from recipes.models import (
    CartItem,
    FavoriteItem,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    Tag,
)
from users.models import Subscription
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAdminAuthorOrReadOnly

User = get_user_model()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ('^name',)


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CustomLimitPagination

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        ['put', 'delete'],
        detail=False,
        url_path='me/avatar',
        permission_classes=(IsAdminAuthorOrReadOnly,)
    )
    def avatar(self, request, *args, **kwargs):
        if request.method == 'PUT':
            serializer = AvatarSerializer(
                instance=request.user,
                data=request.data,
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    serializer.data,
                    status=status.HTTP_200_OK
                )
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        elif request.method == 'DELETE':
            user = request.user
            if user.avatar:
                user.avatar.delete(save=True)
                return Response(
                    {'message': 'Аватар успешно удален'},
                    status=status.HTTP_204_NO_CONTENT
                )
            return Response(
                {'message': 'У пользователя нет аватара'},
                status=status.HTTP_204_NO_CONTENT
            )

    @action(
        ['get'],
        detail=False,
        url_path='subscriptions',
        url_name='subscriptions',
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request, *args, **kwargs):
        user = request.user
        subscriptions = (
            Subscription.objects.filter(user=user)
            .select_related('author')
            .annotate(recipes_count=Count('author__recipes'))
        )
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = SubscribeSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

    @action(['post', 'delete'], detail=True)
    def subscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        user = request.user
        if user == author:
            return Response(
                {'error': 'Вы не можете подписаться/отписаться на/от себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if self.request.method == 'POST':
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {'error': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription = Subscription.objects.create(
                user=user,
                author=author
            )
            serializer = SubscribeSerializer(
                subscription,
                context={'request': request}
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        elif self.request.method == 'DELETE':
            subscription = Subscription.objects.filter(
                user=user,
                author=author
            )
            if not subscription.exists():
                return Response(
                    {'error': 'Вы не подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription.delete()
            return Response(
                {'message': 'Вы успешно отписались от пользователя.'},
                status=status.HTTP_204_NO_CONTENT
            )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminAuthorOrReadOnly,)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAdminAuthorOrReadOnly,)
    pagination_class = CustomLimitPagination
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve', 'get-link'):
            return ReadRecipeSerializer
        return WriteRecipeSerializer

    def get_serializer_context(self):
        return {'request': self.request}

    @action(detail=True, methods=['POST', 'DELETE'], url_path='favorite')
    def favorite(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if FavoriteItem.objects.filter(recipe=recipe, user=user).exists():
                return Response(
                    {
                        'detail':
                        f'Рецепт "{recipe.name}" уже добавлен в избранное.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            FavoriteItem.objects.create(recipe=recipe, user=user)
            serializer = FavoriteRecipeSerializer(
                recipe, context={'request': request}
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            favorite_entry = FavoriteItem.objects.filter(
                recipe=recipe, user=user
            )
            if favorite_entry.exists():
                favorite_entry.delete()
                return Response(
                    {'message': 'Рецепт успешно удален из избранного'},
                    status=status.HTTP_204_NO_CONTENT
                )
            return Response(
                {'detail': f'Рецепт "{recipe.name}" не в избранном.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['POST', 'DELETE'], url_path='shopping_cart')
    def shopping_cart(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if CartItem.objects.filter(recipe=recipe, user=user).exists():
                return Response(
                    {
                        'detail':
                        f'Рецепт "{recipe.name}" уже в карзине.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            CartItem.objects.create(recipe=recipe, user=user)
            serializer = FavoriteRecipeSerializer(
                recipe, context={'request': request}
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            favorite_entry = CartItem.objects.filter(
                recipe=recipe, user=user
            )
            if favorite_entry.exists():
                favorite_entry.delete()
                return Response(
                    {'message': 'Рецепт успешно удален из корзины'},
                    status=status.HTTP_204_NO_CONTENT
                )
            return Response(
                {'detail': f'Рецепт "{recipe.name}" не в карзине.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        try:
            recipe = self.get_object()
            relative_url = f"/api/recipes/{recipe.pk}/"
            short_link = request.build_absolute_uri(relative_url)
            return Response(
                {'short-link': short_link},
                status=status.HTTP_200_OK
            )
        except Http404:
            return Response(
                {'error': 'Рецепт не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception:
            return Response(
                {'error': 'Произошла ошибка при получении ссылки.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
    def download_shopping_list(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response(
                {
                    'detail':
                    'Вы должны быть авторизованы для скачивания списка.'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        cart_items = CartItem.objects.filter(
            user=user).values_list('recipe', flat=True)
        if not cart_items.exists():
            return Response(
                {'detail': 'Ваш список покупок пуст.'},
                status=status.HTTP_400_BAD_REQUEST
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
        response = HttpResponse(shopping_list_text, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response
