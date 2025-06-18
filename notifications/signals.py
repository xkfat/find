from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from .models import Notification
from .firebase import send_push_notification
from missing.models import MissingPerson
from missing.signals import case_status_changed
from location_sharing.signals import location_alert, location_request_sent, location_request_responded
from reports.signals import report_created, report_status_changed
import logging
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)
User = get_user_model()


def send_notification(users, message, target_instance=None, notification_type='system', 
                     push_title=None, push_body=None, push_data=None):

    logger.info(f"Sending {notification_type} notification: {message[:50]}...")
    
    ct = None
    oid = None
    if target_instance is not None:
        ct = ContentType.objects.get_for_model(target_instance)
        oid = target_instance.pk

    if not hasattr(users, '__iter__'):
        users = [users]

    invalid_tokens = []
    notification_count = 0
    push_success_count = 0
    
    for user in users:
        try:
            notification = Notification.objects.create(
                user=user,
                message=message,
                content_type=ct,
                object_id=oid,
                notification_type=notification_type
            )
            notification_count += 1
            logger.debug(f"Database notification created for {user.username} (ID: {notification.id})")
            
            if user.fcm:
                title = push_title or "FindThem"
                body = push_body or message
                data = push_data or {}
                data.update({
                    'notification_id': str(notification.id),
                    'notification_type': notification_type,
                    'target_id': str(oid) if oid else '',
                    'target_model': ct.model if ct else ''
                })
                
                result = send_push_notification(
                    title=title,
                    body=body,
                    fcm_token=user.fcm,
                    data=data
                )
                
                if result.get('success'):
                    push_success_count += 1
                    logger.debug(f"Push notification sent to {user.username}")
                elif result.get('should_remove_token'):
                    invalid_tokens.append(user)
                    logger.warning(f"Invalid FCM token for user {user.username}")
                else:
                    logger.error(f"Failed to send push to {user.username}: {result.get('error')}")
            else:
                logger.debug(f"No FCM token for user {user.username} - skipping push notification")
            
        except Exception as e:
            logger.error(f"Error creating notification for {user.username}: {str(e)}")
    
    if invalid_tokens:
        User.objects.filter(id__in=[u.id for u in invalid_tokens]).update(fcm=None)
        logger.info(f"Cleaned up {len(invalid_tokens)} invalid FCM tokens")
    
    logger.info(f"Notification complete: {notification_count} DB notifications, {push_success_count} push notifications sent")


@receiver(post_save, sender=MissingPerson)
def notify_new_missing_person(sender, instance, created, **kwargs):
    if not created:
        return

    logger.info(f"New missing person reported: {instance.first_name} {instance.last_name}")
    
    ct = ContentType.objects.get_for_model(instance)
    existing_notifications = Notification.objects.filter(
        content_type=ct,
        object_id=instance.pk,
        notification_type='missing_person'
    ).count()
    
    if existing_notifications > 0:
        logger.info(f"Notifications already exist for case {instance.pk}, skipping duplicates")
        return
    
    regular_msg = (
        f" New missing person: \"{instance.first_name} {instance.last_name}\". "
        "Click to view details and help if you can."
    )
    
    send_notification(
        users=User.objects.filter(is_staff=False),
        message=regular_msg,
        target_instance=instance,
        notification_type='missing_person',
        push_title="New Missing Person Case",  
        push_data={
            'person_name': f"{instance.first_name} {instance.last_name}",
            'case_id': str(instance.pk),
            'action': 'view_case'
        }
    )

    admin_msg = (
        f"New MissingPerson case : \"{instance.first_name} {instance.last_name}\" "
        f"(ID {instance.pk}) submitted by {instance.reporter.username if instance.reporter else 'Unknown'}."
    )
    
    send_notification(
        users=User.objects.filter(is_staff=True),
        message=admin_msg,
        target_instance=instance,
        notification_type='missing_person',
        push_title="New Case",
        push_data={
            'person_name': f"{instance.first_name} {instance.last_name}",
            'case_id': str(instance.pk),
            'admin_alert': 'true',
            'action': 'admin_review'
        }
    )

@receiver(case_status_changed)
def notify_case_status_change(sender, instance, old_status, new_status, update, **kwargs):
    logger.info(f"Case status changed for {instance.first_name} {instance.last_name}: {old_status} -> {new_status}")
    
    if instance.reporter:
        ct = ContentType.objects.get_for_model(update)
        existing_notification = Notification.objects.filter(
            user=instance.reporter,
            content_type=ct,
            object_id=update.pk,
            notification_type='case_update'
        ).first()
        
        if existing_notification:
            logger.info(f"Notification already exists for update {update.pk}, skipping duplicate")
            return
        
        push_body = f"Case update: {new_status.replace('_', ' ').title()}"
        
        send_notification(
            users=instance.reporter,
            message=update.message,
            target_instance=update,
            notification_type='case_update',
            push_title="Case Update",
            push_body=push_body,  
            push_data={
                'person_name': f"{instance.first_name} {instance.last_name}",
                'case_id': str(instance.pk),
                'old_status': old_status,
                'new_status': new_status,
                'action': 'view_update'
            }
        )



@receiver(report_created)
def notify_new_report(sender, instance, **kwargs):
    reporter_name = instance.user.username if instance.user else "Anonymous"
    
    logger.info(f"New report created for case {instance.missing_person.pk} by {reporter_name}")

    ct = ContentType.objects.get_for_model(instance)
    existing_notifications = Notification.objects.filter(
        content_type=ct,
        object_id=instance.pk,
        notification_type='report'
    ).count()
    
    if existing_notifications > 0:
        logger.info(f"Notifications already exist for report {instance.pk}, skipping duplicates")
        return

    report_msg = (
        f"New report sighting (ID {instance.pk}) on "
        f"\"{instance.missing_person.first_name} {instance.missing_person.last_name}\" "
        f"submitted by {reporter_name}." 
    )
    report_push_body = f"New report on {instance.missing_person.first_name} {instance.missing_person.last_name}"
    
    send_notification(
        users=User.objects.filter(is_staff=True),
        message=report_msg,
        target_instance=instance,
        notification_type='report',
        push_title="New Report Received",
        push_body=report_push_body,
        push_data={
            'report_id': str(instance.pk),
            'person_name': f"{instance.missing_person.first_name} {instance.missing_person.last_name}",
            'case_id': str(instance.missing_person.pk),
            'reporter': reporter_name,
            'action': 'review_report'
        }
    )

    case_owner = instance.missing_person.reporter
    if case_owner and not case_owner.is_staff:
        case_ct = ContentType.objects.get_for_model(instance.missing_person)
        existing_case_notification = Notification.objects.filter(
            user=case_owner,
            content_type=case_ct,
            object_id=instance.missing_person.pk,
            notification_type='case_update',
            message__icontains="There's an update about your case"
        ).first()
        
        if not existing_case_notification:
            update_msg = "There's an update about your case; we're verifying it."
            send_notification(
                users=case_owner,
                message=update_msg,
                target_instance=instance.missing_person,
                notification_type='case_update',
                push_title="Case Update",
                push_body="New update on your case",
                push_data={
                    'person_name': f"{instance.missing_person.first_name} {instance.missing_person.last_name}",
                    'case_id': str(instance.missing_person.pk),
                    'report_id': str(instance.pk),
                    'action': 'view_case'
                }
            )




@receiver(location_request_sent)
def notify_location_request_sent(sender, instance, **kwargs):
    logger.info(f"Location request sent from {instance.sender.username} to {instance.receiver.username}")
    
    ct = ContentType.objects.get_for_model(instance)
    existing_notification = Notification.objects.filter(
        user=instance.receiver,
        content_type=ct,
        object_id=instance.pk,
        notification_type='location_request'
    ).first()
    
    if existing_notification:
        logger.info(f"Location request notification already exists for request {instance.pk}, skipping duplicate")
        return
    
    message = f"{instance.sender.username} has sent you a location sharing request."
    push_body = f"Location request from {instance.sender.username}"
    
    send_notification(
        users=instance.receiver,
        message=message,
        target_instance=instance,
        notification_type='location_request',
        push_title="Location Sharing Request",
        push_body=push_body,
        push_data={
            'sender_name': instance.sender.username,
            'sender_id': str(instance.sender.pk),
            'request_id': str(instance.pk),
            'action': 'respond_to_request'
        }
    )


@receiver(location_request_responded)
def notify_location_request_responded(sender, instance, new_status, **kwargs):
    logger.info(f"Location request {instance.pk} responded: {new_status}")
    
    ct = ContentType.objects.get_for_model(instance)
    existing_notification = Notification.objects.filter(
        user=instance.sender,
        content_type=ct,
        object_id=instance.pk,
        notification_type='location_response',
        message__icontains=new_status
    ).first()
    
    if existing_notification:
        logger.info(f"Location response notification already exists for request {instance.pk}, skipping duplicate")
        return
    
    status_text = "accepted" if new_status == "accepted" else "declined"
    message = f"{instance.receiver.username} has {status_text} your location sharing request."
    push_body = f"Request {status_text} by {instance.receiver.username}"
    
    send_notification(
        users=instance.sender,
        message=message,
        target_instance=instance,
        notification_type='location_response',
        push_title=f"Location Request {status_text.title()}",
        push_body=push_body,
        push_data={
            'receiver_name': instance.receiver.username,
            'receiver_id': str(instance.receiver.pk),
            'request_id': str(instance.pk),
            'response': new_status,
            'action': 'view_location' if new_status == 'accepted' else 'view_request'
        }
    )


@receiver(location_alert)
def notify_location_alert(sender, instance, recipient, **kwargs):
    logger.info(f"Location alert sent from {instance.username} to {recipient.username}")
    
 
    
    five_minutes_ago = timezone.now() - timedelta(minutes=5)
    ct = ContentType.objects.get_for_model(instance)
    
    recent_alert = Notification.objects.filter(
        user=recipient,
        content_type=ct,
        object_id=instance.pk,
        notification_type='location_alert',
        date_created__gte=five_minutes_ago,
        message__icontains=f"{instance.username} sent you a location alert"
    ).first()
    
    if recent_alert:
        logger.info(f"Recent location alert notification exists for {instance.username} -> {recipient.username}, skipping duplicate")
        return
    
    message = f"{instance.username} sent you a location alert."
    push_body = f"Location alert from {instance.username}"
    
    send_notification(
        users=recipient,
        message=message,
        target_instance=instance,
        notification_type='location_alert',
        push_title="Location Alert",
        push_body=push_body,
        push_data={
            'sender_name': instance.username,
            'sender_id': str(instance.pk),
            'alert_type': 'location_alert',
            'action': 'view_location'
        }
    )