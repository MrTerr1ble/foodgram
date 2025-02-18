import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from recipes.models import (
    CartItem,
    FavoriteItem,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    Tag,
)
from users.models import Subscription

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            img_format, img_str = data.split(';base64,')
            ext = img_format.split('/')[-1]
            data = ContentFile(base64.b64decode(img_str), name=f'image.{ext}')
        return super().to_internal_value(data)


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(allow_null=True, required=False)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj
        ).exists()


class CustomUserCreateSerializer(UserCreateSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'id',
            'name',
            'measurement_unit'
        )
        model = Ingredient


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'id',
            'name',
            'slug'
        )
        model = Tag


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class ReadRecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = CustomUserSerializer()
    ingredients = RecipeIngredientSerializer(
        source='ingredient_recipe',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        model = Recipe

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return FavoriteItem.objects.filter(
                user=user, recipe=obj
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return CartItem.objects.filter(
                user=user, recipe=obj
            ).exists()
        return False


class WriteRecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class WriteRecipeSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    ingredients = WriteRecipeIngredientSerializer(
        many=True,
        label='Ingredients',
        required=True
    )
    image = Base64ImageField(allow_null=True)

    class Meta:
        fields = (
            'id',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )
        model = Recipe

    def handle_recipe_data(self, instance, validated_data):
        tags_data = validated_data.pop('tags', None)
        if tags_data is not None:
            instance.tags.set(tags_data)
        ingredients_data = validated_data.pop('ingredients', None)
        if ingredients_data:
            instance.ingredients.clear()
            ingredient_in_recipe_list = [
                IngredientInRecipe(
                    recipe=instance,
                    ingredient_id=ingredient_data['id'],
                    amount=ingredient_data['amount']
                )
                for ingredient_data in ingredients_data
            ]
            IngredientInRecipe.objects.bulk_create(ingredient_in_recipe_list)

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        tags_data = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('ingredients', None)

        recipe = Recipe.objects.create(**validated_data)

        self.handle_recipe_data(
            recipe,
            {'tags': tags_data, 'ingredients': ingredients_data}
        )

        return recipe

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('ingredients', None)

        errors = {}
        if tags_data is None:
            errors['tags'] = 'Это поле обязательно.'
        if ingredients_data is None:
            errors['ingredients'] = 'Это поле обязательно.'
        if errors:
            raise serializers.ValidationError(errors)

        instance = super().update(instance, validated_data)

        self.handle_recipe_data(
            instance,
            {'tags': tags_data, 'ingredients': ingredients_data}
        )

        return instance

    def to_representation(self, instance):
        serializer = ReadRecipeSerializer(
            instance, context={'request': self.context.get('request')}
        )
        return serializer.data

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Добавьте хотя бы один ингредиент'
            )
        existing_ingredient_ids = set(
            Ingredient.objects.values_list('id', flat=True)
        )
        seen_ingredient_ids = set()
        for ingredient_data in value:
            ingredient_id = ingredient_data.get('id')
            if ingredient_id not in existing_ingredient_ids:
                raise serializers.ValidationError(
                    f'Ингредиент с ID {ingredient_id} не существует.'
                )
            if ingredient_id in seen_ingredient_ids:
                raise serializers.ValidationError(
                    f'Ингредиент с ID {ingredient_id} уже добавлен.'
                )
            seen_ingredient_ids.add(ingredient_id)
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Добавьте хотя бы один тег.'
            )

        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                'Список тегов содержит дубликаты.'
            )

        return value

    def validate_cooking_time(self, value):
        if value < 0:
            raise serializers.ValidationError(
                'Время приготовления не может быть отрицательным.'
            )
        return value


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
        model = Recipe


class SubscribeSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(default=0, read_only=True)
    avatar = Base64ImageField(
        source='author.avatar',
        required=False,
        allow_null=True
    )

    class Meta:
        model = Subscription
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        )

    def validate(self, data):
        user = self.context['request'].user
        author_id = self.context['request'].parser_context['kwargs']['id']
        author = get_object_or_404(User, id=author_id)

        if user == author:
            raise serializers.ValidationError(
                {'error': 'Вы не можете подписаться/отписаться на/от себя.'}
            )
        request_method = self.context['request'].method
        if request_method == 'POST':
            if Subscription.objects.filter(
                user=user, author=author
            ).exists():
                raise serializers.ValidationError(
                    {'error': 'Вы уже подписаны на этого пользователя.'}
                )
        elif request_method == 'DELETE':
            if not Subscription.objects.filter(
                user=user, author=author
            ).exists():
                raise serializers.ValidationError(
                    {'error': 'Вы не подписаны на этого пользователя.'}
                )
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        author_id = self.context['request'].parser_context['kwargs']['id']
        author = get_object_or_404(User, id=author_id)
        subscription = Subscription.objects.create(user=user, author=author)
        return subscription

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return Subscription.objects.filter(
            user=user, author=obj.author
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.GET.get('recipes_limit', '6')
        if isinstance(recipes_limit, str) and recipes_limit.isdigit():
            limit = int(recipes_limit)
        else:
            limit = 6
        recipes = Recipe.objects.filter(author=obj.author)[:limit]
        return FavoriteRecipeSerializer(
            recipes, many=True, context={'request': request}
        ).data
