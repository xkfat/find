from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Notification
from users.models import BasicUser
from .serializers import NotificationSerializer



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_notifications(request):
    notification_type = request.query_params.get('type')
    
    notifications = Notification.objects.filter(user=request.user)
    
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type).order_by('-date_created')
        serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_notification(request, id):
    notification = get_object_or_404(Notification, id=id, user=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.save()
    serializer = NotificationSerializer(notification)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def all_notifications(request):
    notifications = Notification.objects.all().order_by('-date_created')
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def sending_notification(request):
    message = request.data.get('message')
    user_id = request.data.get('receiver')
    notification_type = request.data.get('notification_type', 'system') 
    if not message:
        return Response({'error': 'Message is required.'}, status=status.HTTP_400_BAD_REQUEST)

    if user_id == 'all':
        users = BasicUser.objects.all()
        for user in users: 
            Notification.objects.create(user=user, message=message,                 notification_type=notification_type
)
        return Response({'message': 'notification sent to all users'}, status=status.HTTP_201_CREATED)
    
    else:
        user = get_object_or_404(BasicUser, id=user_id)
        Notification.objects.create(user=user, message=message,             notification_type=notification_type
)
        return Response({'message': 'notification sent successfully'}, status=status.HTTP_201_CREATED)

