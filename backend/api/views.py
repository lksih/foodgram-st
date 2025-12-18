from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from djoser.views import UserViewSet
from django.db.models import Sum

from recipes.models import (
    Recipe, Ingredient, Favorited, ShoppingCart, RecipeIngredient
)
from users.models import Follow
from .serializers import (
    RecipeListSerializer, RecipeCreateUpdateSerializer,
    IngredientSerializer, RecipeMinifiedSerializer,
    AvataredUserWithRecipesSerializer, SetAvatarSerializer,
    SetAvatarResponseSerializer, SetPasswordSerializer,
    RecipeGetShortLinkSerializer, AvataredUserSerializer
)
from .filters import RecipeFilter, IngredientFilter
from .permissions import AuthorOrReadOnlyPermission
from .pagination import PageLimitPagination

User = get_user_model()


class AvataredUserViewSet(UserViewSet):
    """
    Переопределенный UserViewSet от Djoser.
    """
    queryset = User.objects.all().order_by('id')
    serializer_class = AvataredUserSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'pk'
    pagination_class = PageLimitPagination

    def get_permissions(self):
        # Для регистрации (create) и просмотра списка/детализации - доступ всем
        if self.action in ['create', 'list', 'retrieve']:
            return [AllowAny()]

        # Для остальных действий - только аутентифицированным
        return [IsAuthenticated()]

    # Отключаем методы
    def disabled_djoser_method_response(self):
        return Response(
            {'detail': 'Djoser method not allowed.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(['post'], detail=False)
    def reset_password(self, request, *args, **kwargs):
        return self.disabled_djoser_method_response()

    @action(['post'], detail=False)
    def reset_password_confirm(self, request, *args, **kwargs):
        return self.disabled_djoser_method_response()

    @action(['post'], detail=False)
    def set_username(self, request, *args, **kwargs):
        return self.disabled_djoser_method_response()

    @action(['post'], detail=False)
    def reset_username(self, request, *args, **kwargs):
        return self.disabled_djoser_method_response()

    @action(['post'], detail=False)
    def reset_username_confirm(self, request, *args, **kwargs):
        return self.disabled_djoser_method_response()

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Получение текущего пользователя.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar'
    )
    def avatar(self, request):
        """
        Добавление или удаление аватара текущего пользователя.
        """
        if request.method == 'PUT':
            serializer = SetAvatarSerializer(
                request.user,
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                SetAvatarResponseSerializer(
                    request.user,
                    context={'request': request}
                ).data
            )

        elif request.method == 'DELETE':
            if request.user.avatar:
                request.user.avatar.delete()
                request.user.avatar = None
                request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['post'],
    )
    def set_password(self, request):
        """
        Изменение пароля текущего пользователя.
        """
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get']
    )
    def subscriptions(self, request):
        """
        Получение списка подписок текущего пользователя.
        """
        following_ids = request.user.follows.values_list(
            'following_id',
            flat=True
        )
        users = User.objects.filter(id__in=following_ids).order_by('id')

        page = self.paginate_queryset(users)
        if page is not None:
            serializer = AvataredUserWithRecipesSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = AvataredUserWithRecipesSerializer(
            users,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete']
    )
    def subscribe(self, request, pk=None):
        """
        Подписка или отписка от пользователя.
        """
        following = get_object_or_404(User, id=pk)

        if request.method == 'POST':
            if request.user == following:
                return Response(
                    {'error': 'Нельзя подписаться на себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if request.user.follows.filter(following=following).exists():
                return Response(
                    {'error': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            Follow.objects.create(user=request.user, following=following)
            serializer = AvataredUserWithRecipesSerializer(
                following,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            follow = request.user.follows.filter(following=following).first()

            if not follow:
                return Response(
                    {'error': 'Вы не подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all().order_by('id')
    serializer_class = IngredientSerializer
    pagination_class = None
    filterset_class = IngredientFilter

    def get_permissions(self):
        return [AllowAny()]  # Доступ всем


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('-created_at')
    filterset_class = RecipeFilter
    pagination_class = PageLimitPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'get_link']:
            # Просмотр доступен всем
            return [AllowAny()]

        if self.action in ['create', 'favorite', 'download_shopping_cart']:
            # Создание и добавление в избранное/корзину - авторизованным
            return [IsAuthenticated()]

        if self.action in ['update', 'partial_update', 'destroy']:
            # Обновление и удаление - авторам
            return [AuthorOrReadOnlyPermission()]

        return [IsAuthenticatedOrReadOnly()]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeListSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='favorite'
    )
    def favorite(self, request, pk=None):
        """
        Добавление или удаление рецепта из избранного.
        """
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            if request.user.favorites.filter(recipe=recipe).exists():
                return Response(
                    {'error': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            Favorited.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(
                recipe,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            favorite = request.user.favorites.filter(recipe=recipe).first()

            if not favorite:
                return Response(
                    {'error': 'Рецепта нет в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart'
    )
    def shopping_cart(self, request, pk=None):
        """
        Добавление или удаление рецепта из списка покупок.
        """
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            if request.user.shopping_cart.filter(recipe=recipe).exists():
                return Response(
                    {'error': 'Рецепт уже в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(
                recipe,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            shopping_cart = request.user.shopping_cart.filter(
                recipe=recipe
            ).first()

            if not shopping_cart:
                return Response(
                    {'error': 'Рецепта нет в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            shopping_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        """
        Получение короткой ссылки на рецепт.
        """
        recipe = get_object_or_404(Recipe, pk=pk)
        recipe = self.get_object()
        serializer = RecipeGetShortLinkSerializer(
            recipe,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """
        Скачивание списка покупок.
        """
        shopping_cart = request.user.shopping_cart.all()
        recipes = [item.recipe for item in shopping_cart]

        # Получаем ингредиенты из модели RecipeIngredient
        ingredients = RecipeIngredient.objects.filter(
            recipe__in=recipes
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit__title'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by(
            'ingredient__name'
        )

        shopping_list = 'Список покупок:\n\n'
        for i, item in enumerate(ingredients):
            name = item['ingredient__name']
            amount = item['total_amount']
            measurement_unit = item['ingredient__measurement_unit__title']

            shopping_list += (
                f'{i + 1}) {name} — '
                f'{amount} '
                f'{measurement_unit}\n'
            )

        response = HttpResponse(
            shopping_list,
            content_type='text/plain; charset=utf-8'
        )
        filename = 'Список покупок.txt'
        content_disposition = f'attachment; filename=\"{filename}\"'
        response['Content-Disposition'] = content_disposition
        return response
