from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import MissingPerson, CaseUpdate
from notifications.models import Notification

@receiver(pre_save, sender=MissingPerson)
def _cache_old_submission_status(sender, instance, **kwargs):
 
    if not instance.pk:
        instance._old_submission_status = None
    else:
        instance._old_submission_status = MissingPerson.objects.get(pk=instance.pk).submission_status

@receiver(post_save, sender=MissingPerson)
def _create_default_case_updates(sender, instance, created, **kwargs):

    defaults = {
        'active':      "We start investigating your case.",
        'in_progress': "We're looking and verifying your case.",
        'closed':      "Your case has been closed. Thank you for using our service.",
        'rejected':    "Your case submission has been rejected. Please contact support if you believe this is an error.",
    }

    if created:
        CaseUpdate.objects.create(
            case=instance,
            message="Thank you for submitting your case; we've received your information."
        )
        CaseUpdate.objects.create(
            case=instance,
            message=defaults['in_progress']
        )
        return

    old = getattr(instance, '_old_submission_status', None)
    new = instance.submission_status
    if old != new and new in defaults:
        CaseUpdate.objects.create(case=instance, message=defaults[new])

@receiver(post_save, sender=CaseUpdate)
def _notify_user_on_case_update(sender, instance, created, **kwargs):
 
    if not created:
        return
    if instance.case.reporter:
        Notification.objects.create(
            recipient=instance.case.reporter,
            case=instance.case,
            message=instance.message
        )
