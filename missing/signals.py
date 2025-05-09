from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver, Signal
from .models import MissingPerson, CaseUpdate

case_status_changed = Signal()

@receiver(pre_save, sender=MissingPerson)
def _cache_old_submission_status(sender, instance, **kwargs):
 
    if not instance.pk:
        instance._old_submission_status = None
    else:
        instance._old_submission_status = MissingPerson.objects.get(pk=instance.pk).submission_status

@receiver(post_save, sender=MissingPerson)
def _handle_case_updates_and_notifications(sender, instance, created, **kwargs):

    defaults = {
        'active':      "We start investigating your case.",
        'in_progress': "We're looking and verifying your case.",
        'closed':      "Your case has been closed. Thank you for using our service.",
        'rejected':    "Your case submission has been rejected.",
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
    
    old_status = getattr(instance, '_old_submission_status', None)
    new_status = instance.submission_status

    if old_status != new_status and new_status in defaults:
        update = CaseUpdate.objects.create(
            case=instance,
            message=defaults[new_status]
        )
        case_status_changed.send(
            sender=MissingPerson,
            instance=instance,
            old_status=old_status,
            new_status=new_status,
            update=update,
        )
        
    

   

