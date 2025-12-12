from django.urls import include, path
from djoser import views as djoser_views


djoser_urlpatterns = [
    #path('users/', AvataredUserViewSet.as_view({'post': 'create'}), name='user-create'),
    #path('users/me/', AvataredUserViewSet.as_view({'get': 'me'}), name='user-me'),
    path('auth/token/login/', djoser_views.TokenCreateView.as_view(), name='login'),
    path('auth/token/logout/', djoser_views.TokenDestroyView.as_view(), name='logout'),
]

urlpatterns = [
    path('', include(djoser_urlpatterns)),
]
