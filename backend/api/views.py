# api/views.py
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from djoser import views as djoser_views
from django.db.models import Sum, F

from recipes.models import (
    Recipe, Ingredient, Favorited, ShoppingCart, RecipeIngredient
)
from users.models import Follow
from .serializers import (
    RecipeListSerializer, RecipeCreateUpdateSerializer,
    IngredientSerializer, RecipeMinifiedSerializer,
    UserWithRecipesSerializer, SetAvatarSerializer,
    SetAvatarResponseSerializer, SetPasswordSerializer,
    RecipeGetShortLinkSerializer, UserSerializer
)
from .filters import RecipeFilter, IngredientFilter
from .permissions import AuthorOrReadOnlyPermission
from .pagination import PageLimitPagination

User = get_user_model()


class UserViewSet(djoser_views.UserViewSet):
    """
    Переопределенный UserViewSet от Djoser.
    """
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'pk'
    pagination_class = PageLimitPagination

    def get_permissions(self):
        """
        Определяем permissions для разных действий.
        """
        # Для регистрации (create) и просмотра списка/детализации - доступ всем
        if self.action in ['create', 'list', 'retrieve']:
            return [AllowAny()]
        
        # Для обновления, удаления и всех остальных действий - только аутентифицированным
        return [IsAuthenticated()]
    
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
        Один action обрабатывает PUT и DELETE методы.
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
        following_ids = Follow.objects.filter(
            user=request.user
        ).values_list('following_id', flat=True)
        
        users = User.objects.filter(id__in=following_ids).order_by('id')
        
        page = self.paginate_queryset(users)
        if page is not None:
            serializer = UserWithRecipesSerializer(
                page, 
                many=True, 
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        
        serializer = UserWithRecipesSerializer(
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
        Один action обрабатывает POST и DELETE методы.
        """
        following = get_object_or_404(User, id=pk)
        
        if request.method == 'POST':
            if request.user == following:
                return Response(
                    {'error': 'Нельзя подписаться на себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if Follow.objects.filter(user=request.user, following=following).exists():
                return Response(
                    {'error': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            Follow.objects.create(user=request.user, following=following)
            serializer = UserWithRecipesSerializer(
                following, 
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        elif request.method == 'DELETE':
            follow = Follow.objects.filter(
                user=request.user, 
                following=following
            ).first()
            
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
    queryset = Recipe.objects.all().order_by('id')
    filterset_class = RecipeFilter
    pagination_class = PageLimitPagination
    
    def get_permissions(self):
        """
        Определяем permissions для разных действий с рецептами.
        """
        if self.action in ['list', 'retrieve', 'get_link']:
            return [AllowAny()]  # Просмотр доступен всем
        
        if self.action in ['create', 'favorite', 'download_shopping_cart']:
            return [IsAuthenticated()]  # Создание и добавление в избранное/корзину - авторизованным
        
        if self.action in ['update', 'partial_update', 'destroy']:
            return [AuthorOrReadOnlyPermission()]  # Обновление и удаление - авторизованным
        
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
        Один action обрабатывает POST и DELETE методы.
        """
        recipe = get_object_or_404(Recipe, pk=pk)
        
        if request.method == 'POST':
            if Favorited.objects.filter(user=request.user, recipe=recipe).exists():
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
            favorite = Favorited.objects.filter(
                user=request.user, 
                recipe=recipe
            ).first()
            
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
        Один action обрабатывает POST и DELETE методы.
        """
        recipe = get_object_or_404(Recipe, pk=pk)
        
        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=request.user, recipe=recipe).exists():
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
            shopping_cart = ShoppingCart.objects.filter(
                user=request.user, 
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
        shopping_cart = ShoppingCart.objects.filter(user=request.user)
        recipes = [item.recipe for item in shopping_cart]

        # Получаем ингредиенты из модели RecipeIngredient
        ingredients = RecipeIngredient.objects.filter(
            recipe__in=recipes
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit__title'
        ).annotate(total_amount=Sum('amount'))

        shopping_list = "Список покупок:\n\n"
        for i, item in enumerate(ingredients):
            shopping_list += (
                f"{i + 1}) {item['ingredient__name']} — {item['total_amount']} {item['ingredient__measurement_unit__title']}\n"
            )

        response = HttpResponse(
            shopping_list,
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = 'attachment; filename=\"Список покупок.txt\"'
        return response
