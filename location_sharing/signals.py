# location_sharing/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver, Signal
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from .models import LocationRequest, LocationSharing

location_request_sent = Signal()
location_request_responded = Signal()
location_alert = Signal()

@receiver(post_save, sender=LocationRequest)
def handle_location_request(sender, instance, created, **kwargs):
    if created:
            location_request_sent.send(
                 sender=LocationRequest,
                 instance=instance,
            )
    else:
            if instance.status in ['accepted', 'declined']:
                  location_request_responded.send(
                        sender=LocationRequest,
                        instance=instance,
                        new_status=instance.status,
                  )
      
    


def handle_location_alert(sender, recipient, **kwargs):
  if created:
        location_alert.send(
              sender=LocationSharing,
              instance=instance,
        )