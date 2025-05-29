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



@receiver(post_save, sender=Notification)
def send_push_on_create(sender, instance, created, **kwargs):
    print(f"Signal triggered! Created: {created}")
    
    if created:
        try:
            print(f"Sending notification to user: {instance.user.username}")
            
            # Check if user has FCM token
            fcm_token = instance.user.fcm
            print(f"User FCM token: {fcm_token[:20] if fcm_token else 'None'}...")
            
            if fcm_token:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=instance.title,
                        body=instance.message,
                    ),
                    data={
                        'type': instance.notification_type,
                        'id': str(instance.id),
                    },
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