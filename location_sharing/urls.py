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
    path('friends/<int:friend_id>/toggle-sharing/', views.toggle_friend_sharing, name='toggle_friend_sharing'),
    
    # Location data endpoints
    path('locations/', views.get_friends_locations, name='get_friends_locations'),
    path('locations/update/', views.update_my_location, name='update_my_location'),
    
    # User search
    path('search-users/', views.search_users, name='search_users'),

    # Simplified sharing settings - maintaining backward compatibility
    path('settings/', views.toggle_global_sharing, name='toggle_global_sharing'),  # For backward compatibility
    path('settings/global-sharing/', views.toggle_global_sharing, name='toggle_global_sharing'),
    path('settings/current/', views.get_sharing_settings, name='get_sharing_settings'),
]