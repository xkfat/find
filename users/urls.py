from django.urls import path
from .views import register_user, login_user, profile_user, manage_users , change_password, logout_user, firebase_auth_view, validate_fields,delete_account, update_fcm_token, remove_fcm_token

urlpatterns = [
    path('signup/', register_user, name='signup'),
    path('login/', login_user, name='login'),
    path('profile/', profile_user, name='profile'),
    path('profile/change-password/', change_password, name='change-password'),
    path('logout/', logout_user, name='logout'), 
    path('social-auth/', firebase_auth_view, name='firebase_auth'),
    path('api/accounts/validate-fields/', validate_fields, name='validate_fields'),
    path('api/accounts/delete/', delete_account, name='delete_account'),

    path('', manage_users,        name='admin-accounts-list'),
    path('<int:pk>/', manage_users,    name='admin-account-detail'),
    path('update-fcm-token/', update_fcm_token, name='update_fcm_token'),

    path('remove-fcm-token/', remove_fcm_token, name='remove-fcm-token'),

  
]
