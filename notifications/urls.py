# notifications/urls.py - Updated with new endpoints

from django.urls import path
from .views import (
    list_notifications, 
    view_notification, 
    send_custom_notification, 
    all_notifications, 
    delete_notification,
    unread_count,
    mark_all_as_read,
    clear_all_notifications,
    notification_stats, 
     admin_notifications_only,  
    current_admin_notifications,
    mark_notification_as_read
)

urlpatterns = [
    # User notification endpoints
    path('', list_notifications, name='list-notifications'),
    path('unread-count/', unread_count, name='unread-count'),
    path('mark-all-read/', mark_all_as_read, name='mark-all-read'),
    
        path('notifications/<int:id>/', mark_notification_as_read, name='mark-notification-as-read'),

    path('clear-all/', clear_all_notifications, name='clear-all-notifications'),
    path('<int:id>/', view_notification, name='view-notification-detail'),
    path('<int:id>/delete/', delete_notification, name='delete-notification'),
    
    # Admin notification endpoints
    path('admin/all/', all_notifications, name='all_notifications'),
    path('admin/send/', send_custom_notification, name='send_custom_notification'),
    path('admin/stats/', notification_stats, name='notification_stats'),
     path('admin/admin-only/', admin_notifications_only, name='admin_notifications_only'), 
    path('admin/my-notifications/', current_admin_notifications, name='current_admin_notifications'), 
]