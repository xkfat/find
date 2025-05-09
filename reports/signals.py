from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver, Signal
from .models import Report

report_created = Signal()
report_status_changed = Signal()

@receiver(pre_save, sender=Report)
def _cache_old_report_status(sender, instance, **kwargs):

    if instance.pk:
        try:
            old_report = Report.objects.get(pk=instance.pk)
            instance._old_status = old_report.report_status
        except Report.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=Report)
def _emit_report_signals(sender, instance, created, **kwargs):
 
    if created:
        report_created.send(sender=Report, instance=instance)
    else:
        old_status = getattr(instance, '_old_status', None)
        new_status = instance.report_status
        if old_status is not None and old_status != new_status:
            report_status_changed.send(
                sender=Report,
                instance=instance,
                old_status=old_status,
                new_status=new_status
            )
