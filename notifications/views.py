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
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)

    qs = Notification.objects.filter(user=request.user)
    notification_type = request.query_params.get('type')

    if notification_type:
        qs = qs.filter(notification_type=notification_type)
    qs = qs.order_by('-date_created')
    serializer = NotificationSerializer(qs, many=True)
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
    qs = Notification.objects.all().order_by('-date_created')
    serializer = NotificationSerializer(qs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_notification(request, id):
    try:
        notification = get_object_or_404(Notification, id=id, user=request.user)
        notification.delete()
        return Response({'message': 'Notification deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        return Response({'error': 'Failed to delete notification'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_notification(request):
    message = request.data.get('message')
    receiver = request.data.get('receiver')
    notification_type = request.data.get('notification_type', 'system') 
    if not message:
        return Response({'error': 'Message is required.'}, status=status.HTTP_400_BAD_REQUEST)


    valid_types = {choice[0] for choice in Notification.NOTIFICATION_TYPES}
    if notification_type not in valid_types:
        return Response({'error': 'Invalid notification_type.'},
                        status=status.HTTP_400_BAD_REQUEST)
    
    if receiver == 'all':
        users = BasicUser.objects.all()
        for user in users: 
            Notification.objects.create(user=user, message=message, notification_type=notification_type)
        return Response({'message': 'notification sent to all users'}, status=status.HTTP_201_CREATED)
    
    try:
        user_id = int(receiver)
    except (TypeError, ValueError):
        return Response({'error': 'Invalid receiver ID.'}, status=status.HTTP_400_BAD_REQUEST)
    

    user = get_object_or_404(BasicUser, id=user_id)
    Notification.objects.create(user=user, message=message, notification_type=notification_type)
    return Response({'message': 'notification sent successfully'}, status=status.HTTP_201_CREATED)

