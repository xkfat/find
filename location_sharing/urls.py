# location_sharing/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Location requests
    path('requests/', views.get_location_requests, name='location-requests'),
    path('requests/send/', views.send_location_request, name='send-location-request'),
    path('requests/<int:request_id>/accept/', views.accept_location_request, name='accept-location-request'),
    path('requests/<int:request_id>/decline/', views.decline_location_request, name='decline-location-request'),
    
    # Friends management
    path('friends/', views.get_sharing_friends, name='sharing-friends'),
    path('friends/<int:user_id>/alert/', views.send_alert, name='send-alert'),
    path('friends/<int:user_id>/remove/', views.remove_friend, name='remove-friend'),
    
    # Location data
    path('map/', views.get_friends_locations, name='friends-locations'),
    path('my-location/', views.update_my_location, name='update-my-location'),
    
    # Settings
    path('settings/', views.update_sharing_settings, name='update-sharing-settings'),
    path('settings/selected-friends/', views.get_selected_friends, name='selected-friends'),
]