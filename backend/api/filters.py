# api/filters.py
import django_filters
from django.db.models import Q
from recipes.models import Recipe


class RecipeFilter(django_filters.FilterSet):
    is_favorited = django_filters.NumberFilter(
        method='filter_is_favorited',
        label='В избранном'
    )
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_is_in_shopping_cart',
        label='В списке покупок'
    )
    author = django_filters.NumberFilter(
        field_name='author__id',
        label='Автор'
    )
    
    class Meta:
        model = Recipe
        fields = ['author']
    
    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value == 1:
            return queryset.filter(in_favorites__user=user)
        return queryset
    
    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value == 1:
            return queryset.filter(in_shopping_cart__user=user)
        return queryset