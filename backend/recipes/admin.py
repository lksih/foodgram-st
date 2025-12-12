from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Recipe, MeasurementUnit, Ingredient, ShoppingCart, Favorited

admin.site.register(Recipe, UserAdmin)
admin.site.register(MeasurementUnit, UserAdmin)
admin.site.register(Ingredient, UserAdmin)
admin.site.register(ShoppingCart, UserAdmin)
admin.site.register(Favorited, UserAdmin)
