from django.contrib.auth import get_user_model
from django.db.models import Count
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from api.pagination import CustomLimitPagination
from api.serializers import (
    AvatarSerializer,
    CustomUserSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    ReadRecipeSerializer,
    ShoppingCartSerializer,
    SubscribeSerializer,
    TagSerializer,
    WriteRecipeSerializer,
)
from recipes.models import CartItem, FavoriteItem, Ingredient, Recipe, Tag
from users.models import Subscription

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAdminAuthorOrReadOnly
from .utils import generate_shopping_list

User = get_user_model()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ('^name',)


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.annotate(recipes_count=Count('recipes'))
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
        author_id = id
        user = request.user
        if request.method == 'POST':
            # Получаем объект автора
            author = get_object_or_404(User, id=author_id)
            serializer = SubscribeSerializer(
                data={'author': author_id},
                context={'request': request}
            )
            if serializer.is_valid():
                serializer.save(user=user, author=author)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        elif request.method == 'DELETE':
            subscription = Subscription.objects.filter(
                user=user, author_id=author_id
            )

            if subscription.exists():
                subscription.delete()
                return Response(
                    {'message': 'Вы успешно отписались от пользователя.'},
                    status=status.HTTP_204_NO_CONTENT
                )
            return Response(
                {'error': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_404_NOT_FOUND
            )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminAuthorOrReadOnly,)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().select_related(
        'author'
    ).prefetch_related(
        'ingredients', 'tags'
    )
    permission_classes = (IsAdminAuthorOrReadOnly,)
    pagination_class = CustomLimitPagination
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve', 'get-link'):
            return ReadRecipeSerializer
        return WriteRecipeSerializer

    def get_serializer_context(self):
        return {'request': self.request}

    def recipe_post_delete(self, request, pk, model, serializer_class):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            serializer = serializer_class(
                data={
                    'user': request.user.id,
                    'recipe': recipe.id,
                },
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if not model.objects.filter(
                user=request.user,
                recipe=recipe
            ).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            model.objects.filter(
                user=request.user,
                recipe=recipe
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated, ]
    )
    def favorite(self, request, pk):
        return self.recipe_post_delete(
            request,
            pk,
            FavoriteItem,
            FavoriteSerializer
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated, ]
    )
    def shopping_cart(self, request, pk):
        return self.recipe_post_delete(
            request,
            pk,
            CartItem,
            ShoppingCartSerializer
        )

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        try:
            recipe = self.get_object()
            relative_url = f'/recipes/{recipe.pk}/'
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
        buffer = generate_shopping_list(user)
        response = HttpResponse(buffer, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response
