from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from .models import Notification
from missing.models import MissingPerson
from missing.signals import case_status_changed
from location_sharing.signals import location_alert, location_request_sent, location_request_responded
from reports.signals import report_created, report_status_changed

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
        f" New missing person: \"{instance.first_name}  {instance.last_name} \". "
        "Click to view details and help if you can."
    )
    send_notification(
        User.objects.all(),
        help_msg,
        target_instance=instance,
        notification_type='missing_person'

    )

    admin_msg = (
        f"📢 Admin alert: MissingPerson \"{instance.first_name}  {instance.last_name}\" "
        f"(ID {instance.pk}) submitted by {instance.reporter.username}.")
    send_notification(
        User.objects.filter(is_staff=True),
        admin_msg,
        target_instance=instance,
        notification_type='missing_person'

    )


@receiver(report_created)
def notify_new_report(sender, instance, **kwargs):
    reporter_name = instance.user.username if instance.user else "Anonymous"

    report_msg = (
    f"📝 New report (ID {instance.pk}) on "
    f"\"{instance.missing_person.first_name} {instance.missing_person.last_name}\" "
    f"submitted by {reporter_name}." 
)
    send_notification(
        User.objects.filter(is_staff=True),
        report_msg,
        target_instance=instance,
        notification_type='report'
    )

    case_owner = instance.missing_person.reporter
    if case_owner:
        update_msg = "There's an update about your case; we're verifying it."
        send_notification(
            case_owner,
            update_msg,
            target_instance=instance.missing_person,
            notification_type='case_update'
        )

@receiver(case_status_changed)
def notify_case_status_change(sender, instance, old_status, new_status, update, **kwargs):
    if instance.reporter:
        send_notification(
            instance.reporter, 
            update.message,
            target_instance=update,
            notification_type='case_update'
        )

@receiver(location_request_sent)
def notify_location_request_sent(sender, instance, **kwargs):
    send_notification(
        instance.receiver,
        f"{instance.sender.username} has sent you a location sharing request.",
        target_instance=instance,
        notification_type='location_request'
    )

@receiver(location_request_responded)
def notify_location_request_responded(sender, instance, new_status, **kwargs):
    send_notification(
        instance.sender,
        f"{instance.receiver.username} has {new_status} your location sharing request.",
        target_instance=instance,
        notification_type='location_response'
    )


@receiver(location_alert)
def notify_location_alert(sender, instance, recipient, **kwargs):
    send_notification(
        recipient,
        f"{instance.username} sent you a location alert.",
        target_instance=instance,
        notification_type='location_alert'
    )