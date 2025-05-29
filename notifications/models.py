from django.db import models
from users.models import BasicUser
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db.models.signals import post_save
from django.dispatch import receiver
from firebase_admin import messaging

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('system', 'System Notification'),
        ('missing_person', 'Missing Person Notification'),
        ('report', 'Report Notification'),
        ('location_request', 'Location Request'),
        ('location_response', 'Location Response'),
        ('case_update', 'Case Update'),
        ('location_alert', 'Location Alert'),
    )

    user = models.ForeignKey(BasicUser, on_delete=models.CASCADE, related_name='notification')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    date_created = models.DateTimeField(default=timezone.now)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    target = GenericForeignKey('content_type', 'object_id')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, default='system')

    def __str__(self):
        return f"Sent to {self.user.username}"

    @property
    def title(self):
        """Generate title based on notification type"""
        title_map = {
            'missing_person': 'New Missing Person',
            'location_request': 'Location Sharing Request',
            'location_response': 'Location Sharing Accepted',
            'location_alert': 'Location Sharing Alert',
            'case_update': 'Case Update',
            'report': 'Report Update',
            'system': 'FindThem Notification',
        }
        return title_map.get(self.notification_type, 'Notification')


@receiver(post_save, sender=Notification)
def send_push_on_create(sender, instance, created, **kwargs):
    print(f"🔔 Signal triggered! Created: {created}")
    
    if created:
        try:
            print(f"📱 Sending notification to user: {instance.user.username}")
            print(f"📋 Notification type: {instance.notification_type}")
            print(f"📝 Title: {instance.title}")
            
            # Check if user has FCM token
            fcm_token = getattr(instance.user, 'fcm', None)
            print(f"🔑 User FCM token: {fcm_token[:20] if fcm_token else 'None'}...")
            
            if fcm_token:
                # Prepare comprehensive data for Flutter
                push_data = {
                    'notification_id': str(instance.id),
                    'notification_type': instance.notification_type,
                    'user_id': str(instance.user.id),
                    'date_created': instance.date_created.isoformat(),
                    'message': instance.message,
                    'title': instance.title,
                    'body': instance.message,
                    'sender_name': instance.user.username,
                    'receiver_name': instance.user.username,
                    'type': instance.notification_type,  # For compatibility
                    'id': str(instance.id),  # For compatibility
                }
                
                # Add target-specific data if available
                if instance.target:
                    push_data['target_id'] = str(instance.object_id)
                    push_data['target_model'] = instance.content_type.model
                    
                    # Add specific data based on target type
                    if hasattr(instance.target, 'id'):
                        if instance.content_type.model == 'missingperson':
                            push_data['case_id'] = str(instance.target.id)
                        elif instance.content_type.model == 'report':
                            push_data['report_id'] = str(instance.target.id)
                        elif instance.content_type.model == 'locationrequest':
                            push_data['request_id'] = str(instance.target.id)
                
                print(f"📦 Push data keys: {list(push_data.keys())}")
                
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=instance.title,
                        body=instance.message,
                    ),
                    data=push_data,
                    token=fcm_token,
                )
                
                response = messaging.send(message)
                print(f"✅ Push notification sent successfully: {response}")
                
            else:
                print("❌ No FCM token found for user")
                
        except Exception as e:
            print(f"❌ Error sending push notification: {e}")
            import traceback
            traceback.print_exc()