from django.urls import path
from .views import list_notifications, view_notification, send_notification, all_notifications, delete_notification


urlpatterns = [
    path('',list_notifications, name='list-notifications'),
    path('<int:id>/', view_notification, name='view-notification-detail'),
    path('send/', send_notification, name='send-notification'),
    path('all/', all_notifications, name='all-notifications'),
    path('<int:id>/delete/', delete_notification, name='delete-notification'),

]