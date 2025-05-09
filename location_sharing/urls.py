# location_sharing/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Location request endpoints
    path('requests/', views.get_pending_requests, name='get_pending_requests'),
    path('requests/send/', views.send_location_request, name='send_location_request'),
    path('requests/<int:request_id>/respond/', views.respond_to_request, name='respond_to_request'),
    
    # Friend management endpoints
    path('friends/', views.get_friends, name='get_friends'),
    path('friends/<int:friend_id>/remove/', views.remove_friend, name='remove_friend'),
    path('friends/<int:friend_id>/alert/', views.send_alert, name='send_alert'),
    
    # Location data endpoints
    path('locations/', views.get_friends_locations, name='get_friends_locations'),
    path('locations/update/', views.update_my_location, name='update_my_location'),
    
    # Sharing settings endpoints
    path('settings/', views.update_sharing_settings, name='update_sharing_settings'),
    path('settings/selected-friends/', views.get_selected_friends, name='get_selected_friends'),
    path('settings/current/', views.get_sharing_settings, name='get_sharing_settings'),

]