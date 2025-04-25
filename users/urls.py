from django.urls import path
from .views import register_user, login_user, profile_user, manage_users , change_password

urlpatterns = [
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),
    path('profile/', profile_user, name='profile'),
    path('profile/change-password/', change_password, name='change-password'),


    path('admin/accounts/', manage_users,        name='admin-accounts-list'),
    path('admin/accounts/<int:pk>/', manage_users,    name='admin-account-manage'),
  
]
