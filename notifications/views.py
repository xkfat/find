from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Notification
from users.models import BasicUser
from .serializers import NotificationSerializer
from .signals import send_notification
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_notifications(request):
   
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    if unread_count > 0:
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        logger.info(f"Marked {unread_count} notifications as read for {request.user.username}")

    qs = Notification.objects.filter(user=request.user)
    notification_type = request.query_params.get('type')
    
    if notification_type:
        qs = qs.filter(notification_type=notification_type)
    
    qs = qs.order_by('-date_created')
    serializer = NotificationSerializer(qs, many=True)
    
    return Response({
        'notifications': serializer.data,
        'marked_read': unread_count
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unread_count(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return Response({'unread_count': count})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_notification(request, id):
    notification = get_object_or_404(Notification, id=id, user=request.user)
    
    if not notification.is_read:
        notification.is_read = True
        notification.save()
        logger.info(f"Notification {id} marked as read for {request.user.username}")
    
    serializer = NotificationSerializer(notification)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def all_notifications(request):
    qs = Notification.objects.all().order_by('-date_created')
    
    user_id = request.query_params.get('user_id')
    notification_type = request.query_params.get('type')
    
    if user_id:
        qs = qs.filter(user_id=user_id)
    if notification_type:
        qs = qs.filter(notification_type=notification_type)
    
    serializer = NotificationSerializer(qs, many=True)
    return Response(serializer.data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_notification(request, id):
    try:
        notification = get_object_or_404(Notification, id=id, user=request.user)
        notification.delete()
        logger.info(f"Notification {id} deleted by {request.user.username}")
        return Response({'message': 'Notification deleted successfully'}, 
                       status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.error(f"Failed to delete notification {id}: {str(e)}")
        return Response({'error': 'Failed to delete notification'}, 
                       status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_all_notifications(request):
    try:
        count = Notification.objects.filter(user=request.user).count()
        Notification.objects.filter(user=request.user).delete()
        logger.info(f"Cleared {count} notifications for {request.user.username}")
        return Response({'message': f'Cleared {count} notifications'}, 
                       status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Failed to clear notifications for {request.user.username}: {str(e)}")
        return Response({'error': 'Failed to clear notifications'}, 
                       status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_custom_notification(request):
    message = request.data.get('message')
    receiver = request.data.get('receiver')
    notification_type = request.data.get('notification_type', 'system')
    push_title = request.data.get('push_title', 'FindThem')
    
    if not message:
        return Response({'error': 'Message is required.'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    valid_types = {choice[0] for choice in Notification.NOTIFICATION_TYPES}
    if notification_type not in valid_types:
        return Response({'error': 'Invalid notification_type.'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        if receiver == 'all':
            users = BasicUser.objects.all()
            user_count = users.count()
            
            send_notification(
                users=users,
                message=message,
                notification_type=notification_type,
                push_title=push_title
            )
            
            logger.info(f"Admin {request.user.username} sent notification to all {user_count} users")
            return Response({
                'message': f'Notification sent to all {user_count} users',
                'recipients': user_count
            }, status=status.HTTP_201_CREATED)
        
        elif receiver == 'staff':
            # Handle staff only option
            users = BasicUser.objects.filter(is_staff=True)
            user_count = users.count()
            
            send_notification(
                users=users,
                message=message,
                notification_type=notification_type,
                push_title=push_title
            )
            
            logger.info(f"Admin {request.user.username} sent notification to {user_count} staff users")
            return Response({
                'message': f'Notification sent to {user_count} staff users',
                'recipients': user_count
            }, status=status.HTTP_201_CREATED)
        
        else:
            # Handle specific users (array of IDs)
            if isinstance(receiver, list):
                user_ids = receiver
            else:
                # Single user ID
                try:
                    user_ids = [int(receiver)]
                except (TypeError, ValueError):
                    return Response({'error': 'Invalid receiver format.'}, 
                                   status=status.HTTP_400_BAD_REQUEST)
            
            # Get all users with the specified IDs
            users = BasicUser.objects.filter(id__in=user_ids)
            user_count = users.count()
            
            if user_count == 0:
                return Response({'error': 'No valid users found with provided IDs.'}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            send_notification(
                users=users,
                message=message,
                notification_type=notification_type,
                push_title=push_title
            )
            
            logger.info(f"Admin {request.user.username} sent notification to {user_count} specific users")
            return Response({
                'message': f'Notification sent to {user_count} users',
                'recipients': user_count,
                'user_ids': list(users.values_list('id', flat=True))
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        logger.error(f"Failed to send custom notification: {str(e)}")
        return Response({'error': f'Failed to send notification: {str(e)}'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)