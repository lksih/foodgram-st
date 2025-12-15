from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Recipe, MeasurementUnit, Ingredient, ShoppingCart, Favorited

admin.site.register(Recipe)
admin.site.register(Ingredient)
admin.site.register(MeasurementUnit)
admin.site.register(Favorited)
admin.site.register(ShoppingCart)