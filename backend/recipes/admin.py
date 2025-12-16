from django.contrib import admin
from .models import (
    MeasurementUnit,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Favorited,
    ShoppingCart,
)


class MeasurementUnitAdmin(admin.ModelAdmin):
    """Админка для модели единиц измерения."""

    list_display = ("title",)
    search_fields = ("title",)


class IngredientAdmin(admin.ModelAdmin):
    """Админка для модели ингредиентов."""

    list_display = ("name", "measurement_unit")
    search_fields = ("name",)
    list_filter = ("measurement_unit",)


class RecipeIngredientInline(admin.TabularInline):
    """Встроенное отображение ингредиентов рецепта."""

    model = RecipeIngredient
    extra = 1
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    """Админка для модели рецептов."""

    list_display = ("name", "author", "favorites_count")
    search_fields = ("name", "author__username", "author__first_name",
                     "author__last_name", "author__email")
    list_filter = ("author",)
    inlines = (RecipeIngredientInline,)
    readonly_fields = ("favorites_count",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "author",
                    "image",
                    "text",
                    "favorites_count",
                    "cooking_time",
                )
            },
        ),
    )

    def favorites_count(self, obj):
        """Возвращает количество добавлений рецепта в избранное."""
        return obj.in_favorites.count()

    favorites_count.short_description = "Количество добавлений в избранное"


class RecipeIngredientAdmin(admin.ModelAdmin):
    """Админка для модели связи рецепта и ингредиентов."""

    list_display = ("recipe", "ingredient", "amount")
    search_fields = ("recipe__name", "ingredient__name")
    list_filter = ("recipe", "ingredient")


class FavoritedAdmin(admin.ModelAdmin):
    """Админка для модели избранного."""

    list_display = ("user", "recipe")
    search_fields = ("user__username", "user__email", "recipe__name")
    list_filter = ("user", "recipe")


class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка для модели списка покупок."""

    list_display = ("user", "recipe")
    search_fields = ("user__username", "user__email", "recipe__name")
    list_filter = ("user", "recipe")


admin.site.register(MeasurementUnit, MeasurementUnitAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Favorited, FavoritedAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(RecipeIngredient, RecipeIngredientAdmin)
