from django.contrib import admin
from .models import (
    MeasurementUnit, Ingredient,
    Recipe, RecipeIngredient, Favorited, ShoppingCart
)


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


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'cooking_time')
    search_fields = ('name', 'author__username', 'author__email')
    inlines = [RecipeIngredientInline]


class FavoritedAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'recipe_author')
    search_fields = ('user__username', 'recipe__name')

    def recipe_author(self, obj):
        return obj.recipe.author
    recipe_author.short_description = 'Автор рецепта'


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'recipe_author')
    search_fields = ('user__username', 'recipe__name')

    def recipe_author(self, obj):
        return obj.recipe.author
    recipe_author.short_description = 'Автор рецепта'


admin.site.register(MeasurementUnit, MeasurementUnitAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Favorited, FavoritedAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
