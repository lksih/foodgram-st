from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),

    # Редирект коротких ссылок
    path('s/<int:pk>/',
         RedirectView.as_view(
             pattern_name='recipe-detail',
             permanent=False
         ),
         name='short-link-redirect'),
]
