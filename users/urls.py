from django.urls import path
from .views import Register_user, login_user, profile_user
from rest_framework_simplejwt.views import  TokenObtainPairView, TokenRefreshView


urlpatterns = [
    path('register/', Register_user, name='register'),
    path('login/', login_user, name='login'),
    path('profile/', profile_user, name='profile'),

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
