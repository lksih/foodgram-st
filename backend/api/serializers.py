import base64

from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from rest_framework import serializers
from djoser.serializers import UserCreateSerializer
from djoser.serializers import UserSerializer
from recipes.models import (
    Recipe, Ingredient,
    MeasurementUnit, RecipeIngredient
)

MIN_AMOUNT = 1
MAX_AMOUNT = 32000

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class MeasurementUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementUnit
        fields = ['title']


class IngredientSerializer(serializers.ModelSerializer):
    measurement_unit = serializers.StringRelatedField()

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit.title',
        read_only=True
    )
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT,
        max_value=MAX_AMOUNT
    )

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class AvataredUserSerializer(UserSerializer):
    """
    Сериализатор пользователя на основе Djoser.
    Добавляем поля is_subscribed и avatar.
    """
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = [
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar'
        ]

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.follows.filter(following=obj).exists()
        return False

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar:
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


class AvataredUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = [
            'email', 'id', 'username', 'first_name',
            'last_name', 'password'
        ]


class RecipeListSerializer(serializers.ModelSerializer):
    author = AvataredUserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        ]

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.favorites.filter(recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.shopping_cart.filter(recipe=obj).exists()
        return False

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class IngredientInRecipeCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT,
        max_value=MAX_AMOUNT
    )

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'amount']


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeCreateSerializer(
        many=True,
        write_only=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'ingredients', 'image', 'name',
            'text', 'cooking_time'
        ]

    def validate(self, data):
        """
        Проверка на уровне всего объекта.
        Необходимо проверить наличие нужных полей в PATCH.
        """
        request = self.context.get('request')

        if request:
            if request.method == 'PATCH':
                for field in ['ingredients', 'name', 'text', 'cooking_time']:
                    if field not in data:
                        raise serializers.ValidationError({
                            field: 'Это поле обязательно для создания рецепта'
                        })

        return data

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                "Добавьте хотя бы один ингредиент"
            )

        ingredients = set()
        for ingredient_data in value:
            ingredient = ingredient_data.get('ingredient')
            amount = ingredient_data.get('amount')

            if not ingredient or not amount:
                raise serializers.ValidationError(
                    "Каждый ингредиент должен содержать id и amount"
                )

            if ingredient in ingredients:
                raise serializers.ValidationError(
                    "Ингредиенты не должны повторяться"
                )

            ingredients.add(ingredient)

        return value

    def parse_and_create_ingredients(self, recipe, ingredients_data):
        recipe_ingredients = []
        for ingredient_data in ingredients_data:
            recipe_ingredients.append(RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient_data['ingredient'].id,
                amount=ingredient_data['amount']
            ))

        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        validated_data.pop('author', None)
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )

        self.parse_and_create_ingredients(recipe, ingredients_data)

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.parse_and_create_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        return RecipeListSerializer(
            instance,
            context=self.context
        ).data


class AvataredUserWithRecipesSerializer(AvataredUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(AvataredUserSerializer.Meta):
        fields = (AvataredUserSerializer.Meta.fields
                  + ['recipes', 'recipes_count'])

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')

        recipes = obj.recipes.all()
        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except ValueError:
                pass

        return RecipeMinifiedSerializer(
            recipes,
            many=True,
            context=self.context
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SetAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ['avatar']


class SetAvatarResponseSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['avatar']

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar:
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField()
    current_password = serializers.CharField()

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Неверный текущий пароль")
        return value


class RecipeGetShortLinkSerializer(serializers.Serializer):
    class Meta:
        model = Recipe
        fields = []

    def to_representation(self, instance):
        """
        Генерирует короткую ссылку.
        """
        request = self.context.get('request')
        if request:
            base_url = request.build_absolute_uri('/')
        else:
            base_url = 'https://foodgram.example.org/'

        return {
            'short-link': f"{base_url}s/{instance.id}"
        }
