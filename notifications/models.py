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
