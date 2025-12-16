from django.urls import path, include
from rest_framework.routers import DefaultRouter
from djoser.views import TokenCreateView, TokenDestroyView
from django.views.generic import RedirectView

from .views import (
    AvataredUserViewSet, RecipeViewSet, IngredientViewSet
)

router = DefaultRouter()
router.register('users', AvataredUserViewSet, basename='user')
router.register('recipes', RecipeViewSet, basename='recipe')
router.register('ingredients', IngredientViewSet, basename='ingredient')

urlpatterns = [
    path('', include(router.urls)),

    # Эндпоинты Djoser для токенов
    path('auth/token/login/', TokenCreateView.as_view(), name='login'),
    path('auth/token/logout/', TokenDestroyView.as_view(), name='logout'),

    # Редирект коротких ссылок
    path('s/<int:pk>/',
         RedirectView.as_view(
             pattern_name='recipe-detail',
             permanent=False
         ),
         name='short-link-redirect'),
]
