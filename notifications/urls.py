from django.urls import path
from .views import list_notifications, view_notification, send_notification, all_notifications


urlpatterns = [
    path('', list_notifications, name='list-notifications'),
    path('<int:id>/', view_notification, name='view-notification-detail'),
    path('send/', send_notification, name='send-notification'),
    path('all/', all_notifications, name='all-notifications'),
]