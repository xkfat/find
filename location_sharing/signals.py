# location_sharing/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from .models import LocationRequest, LocationSharing

@receiver(post_save, sender=LocationRequest)
def notify_location_request(sender, instance, created, **kwargs):
    """Send notification when a location request is created or updated"""
    if created:
        # Send notification to receiver about new request
        Notification = apps.get_model('notifications', 'Notification')
        Notification.objects.create(
            user=instance.receiver,
            message=f"{instance.sender.username} has sent you a location sharing request.",
            notification_type='location_request',
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id
        )
    elif not created and instance.status in ['accepted', 'declined']:
        # Send notification to sender about request response
        Notification = apps.get_model('notifications', 'Notification')
        Notification.objects.create(
            user=instance.sender,
            message=f"{instance.receiver.username} has {instance.status} your location sharing request.",
            notification_type='location_response',
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id
        )


def send_location_alert(sender, recipient, **kwargs):
    """Send a location alert notification to a friend"""
    Notification = apps.get_model('notifications', 'Notification')
    Notification.objects.create(
        user=recipient,
        message=f"{sender.username} sent you a location alert",
        notification_type='location_request',
        content_type=ContentType.objects.get_for_model(sender),
        object_id=sender.id
    )