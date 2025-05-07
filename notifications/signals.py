# notifications/signals.py

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from .models import Notification
from missing.models import MissingPerson
from reports.models import Report

User = get_user_model()


def send_notification(users, message, target_instance=None, notification_type='system'):
    ct = None
    oid = None
    if target_instance is not None:
        ct = ContentType.objects.get_for_model(target_instance)
        oid = target_instance.pk

    if not hasattr(users, '__iter__'):
        users = [users]

    for u in users:
        Notification.objects.create(
            user=u,
            message=message,
            content_type=ct,
            object_id=oid,
            notification_type=notification_type
        )


@receiver(post_save, sender=MissingPerson)
def notify_new_missing_person(sender, instance, created, **kwargs):
    if not created:
        return

    help_msg = (
        f"🔔 New missing person: “{instance.first_name}  {instance.last_name} ”. "
        "Click to view details and help if you can."
    )
    send_notification(
        User.objects.all(),
        help_msg,
        target_instance=instance,
        notification_type='missing_person'

    )

    admin_msg = (
        f"📢 Admin alert: MissingPerson “{instance.first_name}  {instance.last_name}” "
        f"(ID {instance.pk}) submitted by {instance.reporter.username}."
    )
    send_notification(
        User.objects.filter(is_staff=True),
        admin_msg,
        target_instance=instance,
        notification_type='missing_person'

    )


@receiver(post_save, sender=Report)
def notify_new_report(sender, instance, created, **kwargs):
    if not created:
        return

    report_msg = (
    f"📝 New report (ID {instance.pk}) on “"
    f"{instance.missing_person.first_name} {instance.missing_person.last_name}” "
    f"submitted by {instance.user.username}."
)
    send_notification(
        User.objects.filter(is_staff=True),
        report_msg,
        target_instance=instance,
        notification_type='report'

    )



