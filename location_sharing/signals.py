from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps
from .models import LocationRequest, LocationSharing

@receiver(post_save, sender=LocationRequest)
def handle_location_request_status_change(sender, instance, created, **kwargs):
    """Send notifications when a location request is created or its status changes"""
    Notification = apps.get_model('notifications', 'Notification')
    
    # New request created
    if created:
        Notification.objects.create(
            user=instance.receiver,
            type='location_request_received',
            message=f"{instance.sender.username} wants to share location with you",
            related_id=instance.id
        )
    
    # Request accepted (handle in case it's modified directly without using views)
    elif instance.status == 'accepted' and not kwargs.get('raw', False):
        # Create bidirectional sharing if it doesn't exist
        if not LocationSharing.objects.filter(user=instance.sender, friend=instance.receiver).exists():
            LocationSharing.objects.get_or_create(user=instance.sender, friend=instance.receiver)
        
        if not LocationSharing.objects.filter(user=instance.receiver, friend=instance.sender).exists():
            LocationSharing.objects.get_or_create(user=instance.receiver, friend=instance.sender)
        
        # Notify sender of acceptance
        Notification.objects.create(
            user=instance.sender,
            type='location_request_accepted',
            message=f"{instance.receiver.username} accepted your location sharing request",
            related_id=instance.id
        )


@receiver(post_save, sender=LocationSharing)
def notify_location_sharing_created(sender, instance, created, **kwargs):
    """Notify users when location sharing is established"""
    if created and not kwargs.get('raw', False):
        Notification = apps.get_model('notifications', 'Notification')
        Notification.objects.create(
            user=instance.friend,
            type='location_sharing_started',
            message=f"{instance.user.username} is now sharing location with you",
            related_id=instance.id
        )


@receiver(post_delete, sender=LocationSharing)
def notify_location_sharing_removed(sender, instance, **kwargs):
    """Notify users when location sharing is removed"""
    Notification = apps.get_model('notifications', 'Notification')
    Notification.objects.create(
        user=instance.friend,
        type='location_sharing_ended',
        message=f"{instance.user.username} has stopped sharing location with you"
    )