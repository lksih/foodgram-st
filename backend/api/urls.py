# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from djoser.views import TokenCreateView, TokenDestroyView

from .views import (
    UserViewSet, RecipeViewSet, IngredientViewSet, FollowViewSet
)

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet, basename='ingredients')

# Для FollowViewSet регистрируем отдельно, так как это ViewSet
follow_list = FollowViewSet.as_view({'get': 'list'})
follow_detail = FollowViewSet.as_view({'post': 'subscribe', 'delete': 'subscribe'})

urlpatterns = [
    path('', include(router.urls)),
    
    # Эндпоинты для подписок
    path('users/subscriptions/', follow_list, name='subscriptions'),
    path('users/<int:pk>/subscribe/', follow_detail, name='subscribe'),
    
    # Эндпоинты Djoser для токенов
    path('auth/token/login/', TokenCreateView.as_view(), name='login'),
    path('auth/token/logout/', TokenDestroyView.as_view(), name='logout'),
]
