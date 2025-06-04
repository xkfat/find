# notifications/views.py - Updated with additional endpoints

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
    """
    Get notifications for the authenticated user
    Automatically marks unread notifications as read when fetched
    """
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
    """Get count of unread notifications for the user"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return Response({'unread_count': count})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_as_read(request):
    """Mark all notifications as read for the user"""
    updated_count = Notification.objects.filter(
        user=request.user, 
        is_read=False
    ).update(is_read=True)
    
    logger.info(f"Marked {updated_count} notifications as read for {request.user.username}")
    
    return Response({
        'message': f'Marked {updated_count} notifications as read',
        'updated_count': updated_count
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_notification(request, id):
    """Get a specific notification and mark it as read"""
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
    """Get all notifications (admin only)"""
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
    """Delete a specific notification"""
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
    """Clear all notifications for the user"""
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
    """Send custom notification (admin only)"""
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

@api_view(['GET'])
@permission_classes([IsAdminUser])
def notification_stats(request):
    """Get notification statistics (admin only)"""
    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import timedelta
    
    try:
        # Total notifications
        total_notifications = Notification.objects.count()
        
        # Unread notifications
        unread_notifications = Notification.objects.filter(is_read=False).count()
        
        # Notifications by type
        type_stats = Notification.objects.values('notification_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Recent notifications (last 24 hours)
        yesterday = timezone.now() - timedelta(days=1)
        recent_notifications = Notification.objects.filter(
            date_created__gte=yesterday
        ).count()
        
        # Top active users (most notifications)
        top_users = Notification.objects.values(
            'user__username'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        return Response({
            'total_notifications': total_notifications,
            'unread_notifications': unread_notifications,
            'recent_notifications_24h': recent_notifications,
            'notifications_by_type': type_stats,
            'top_users': top_users,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to fetch notification stats: {str(e)}")
        return Response({
            'error': f'Failed to fetch notification stats: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
# Add this view to your notifications/views.py

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_notifications_only(request):
    """
    Get notifications specifically sent TO admin users
    This returns only notifications where the recipient is an admin
    """
    # Get notifications for admin users only
    qs = Notification.objects.filter(
        user__is_staff=True  # Only notifications sent to admin users
    ).select_related('user').order_by('-date_created')
    
    # Apply filters
    notification_type = request.query_params.get('type')
    is_read = request.query_params.get('is_read')
    user_id = request.query_params.get('user_id')
    
    if notification_type:
        qs = qs.filter(notification_type=notification_type)
    
    if is_read is not None:
        is_read_bool = is_read.lower() in ['true', '1', 'yes']
        qs = qs.filter(is_read=is_read_bool)
    
    if user_id:
        qs = qs.filter(user_id=user_id)
    
    serializer = NotificationSerializer(qs, many=True)
    
    return Response({
        'notifications': serializer.data,
        'count': qs.count(),
        'admin_only': True
    })

@api_view(['GET']) 
@permission_classes([IsAdminUser])
def current_admin_notifications(request):
    """
    Get notifications for the currently logged-in admin user
    This is what you probably want for the admin dashboard
    """
    if not request.user.is_staff:
        return Response(
            {'error': 'Only admin users can access this endpoint'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get notifications for the current admin user
    qs = Notification.objects.filter(user=request.user).order_by('-date_created')
    
    # Apply filters
    notification_type = request.query_params.get('type')
    if notification_type:
        qs = qs.filter(notification_type=notification_type)
    
    serializer = NotificationSerializer(qs, many=True)
    
    # Count unread notifications
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    return Response({
        'notifications': serializer.data,
        'unread_count': unread_count,
        'total_count': qs.count(),
        'user': request.user.username
    })

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def mark_notification_as_read(request, id):
    """Mark a specific notification as read via PATCH"""
    try:
        notification = get_object_or_404(Notification, id=id, user=request.user)
        
        is_read = request.data.get('is_read', True)
        notification.is_read = is_read
        notification.save()
        
        logger.info(f"Notification {id} marked as {'read' if is_read else 'unread'} for {request.user.username}")
        
        serializer = NotificationSerializer(notification)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Failed to update notification {id}: {str(e)}")
        return Response({'error': 'Failed to update notification'}, 
                       status=status.HTTP_400_BAD_REQUEST)