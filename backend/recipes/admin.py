from django.contrib import admin
from .models import (
    MeasurementUnit, Ingredient,
    Recipe, RecipeIngredient, Favorited, ShoppingCart
)

@admin.register(MeasurementUnit)
class MeasurementUnitAdmin(admin.ModelAdmin):
    list_display = ('title', 'ingredient_count')
    search_fields = ('title',)
    
    def ingredient_count(self, obj):
        return obj.ingredients.count()
    ingredient_count.short_description = 'Количество ингредиентов'


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)



@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'cooking_time')
    search_fields = ('name', 'author__username', 'author__email')
    inlines = [RecipeIngredientInline]


@admin.register(Favorited)
class FavoritedAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'recipe_author')
    search_fields = ('user__username', 'recipe__name')
    
    def recipe_author(self, obj):
        return obj.recipe.author
    recipe_author.short_description = 'Автор рецепта'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'recipe_author')
    search_fields = ('user__username', 'recipe__name')
    
    def recipe_author(self, obj):
        return obj.recipe.author
    recipe_author.short_description = 'Автор рецепта'