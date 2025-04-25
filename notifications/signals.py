# notifications/signals.py

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from missing.models import MissingPerson
from reports.models import Report
from .models import Notification

User = get_user_model()


def send_notification(users, message, target_instance=None):
    """
    Create a Notification for one user or an iterable of users,
    optionally pointing at a model instance via a GenericForeignKey.
    """
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
            object_id=oid
        )


# 1. New MissingPerson created → notify all users to help + admins of submission
@receiver(post_save, sender=MissingPerson)
def notify_new_missing_person(sender, instance, created, **kwargs):
    if not created:
        return

    # A) Notify everyone to help
    help_msg = (
        f"🔔 New missing person: “{instance.first_name}  {instance.last_name} ”. "
        "Click to view details and help if you can."
    )
    send_notification(
        User.objects.all(),
        help_msg,
        target_instance=instance
    )

    # B) Notify admins of new submission
    admin_msg = (
        f"📢 Admin alert: MissingPerson “{instance.first_name}  {instance.last_name}” "
        f"(ID {instance.pk}) submitted by {instance.reporter.username}."
    )
    send_notification(
        User.objects.filter(is_staff=True),
        admin_msg,
        target_instance=instance
    )


# 2. New Report created → notify admins to review
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
        target_instance=instance
    )


# 3. MissingPerson status change → notify the original reporter
@receiver(pre_save, sender=MissingPerson)
def notify_status_change(sender, instance, **kwargs):
    if not instance.pk:
        # skip creation
        return

    try:
        previous = MissingPerson.objects.get(pk=instance.pk)
    except MissingPerson.DoesNotExist:
        return

    if previous.status != instance.status:
        status_msg = (
            f"ℹ️ Status update for “{instance.name}”: "
            f"{previous.status} → {instance.status}."
        )
        send_notification(
            instance.reporter,
            status_msg,
            target_instance=instance
        )
