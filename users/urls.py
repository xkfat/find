from django.urls import path
from .views import register_user, login_user, profile_user, manage_users , change_password, logout_user, firebase_auth_view

urlpatterns = [
    path('signup/', register_user, name='signup'),
    path('login/', login_user, name='login'),
    path('profile/', profile_user, name='profile'),
    path('profile/change-password/', change_password, name='change-password'),
    path('logout/', logout_user, name='logout'), 
    path('firebase-auth/', firebase_auth_view, name='firebase_auth'),

    path('', manage_users,        name='admin-accounts-list'),
    path('<int:pk>/', manage_users,    name='admin-account-detail'),
  
]
