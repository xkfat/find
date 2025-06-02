from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver, Signal
from django.db import transaction
from .models import MissingPerson, CaseUpdate
import threading

case_status_changed = Signal()

def process_face_matching_background(person_id):
    """Background task to process face matching - moved from views.py"""
    import time
    
    # Add a small delay to ensure the transaction is committed
    time.sleep(1)
    
    try:
        from .views import auto_face_match_on_creation
        
        # Try to get the person with retry logic
        max_retries = 3
        person = None
        
        for attempt in range(max_retries):
            try:
                person = MissingPerson.objects.get(id=person_id)
                break
            except MissingPerson.DoesNotExist:
                if attempt < max_retries - 1:
                    print(f"⏳ Person ID {person_id} not found, retrying in 2 seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(2)
                else:
                    print(f"❌ Person with ID {person_id} not found after {max_retries} attempts")
                    return
        
        if not person:
            print(f"❌ Could not retrieve person with ID {person_id}")
            return
            
        print(f"🔄 Starting background AI face matching for {person.full_name}...")
        
        face_matches = auto_face_match_on_creation(person)
        
        if face_matches:
            try:
                from notifications.signals import send_notification
                from django.contrib.auth import get_user_model
                
                User = get_user_model()
                admin_users = User.objects.filter(is_staff=True)
                
                message = f"🔍 {len(face_matches)} potential face matches found for {person.full_name}. Please review."
                
                send_notification(
                    users=admin_users,
                    message=message,
                    target_instance=person,
                    notification_type='missing_person',
                    push_title="Face Match Alert",
                    push_data={'person_id': str(person.id), 'match_count': len(face_matches)}
                )
                print(f"📧 Notification sent to {admin_users.count()} admin users")
                
            except Exception as e:
                print(f"⚠️ Error sending notification: {e}")
            
        print(f"✅ Background face matching complete: {len(face_matches)} matches for {person.full_name}")
        
    except Exception as e:
        print(f"❌ Background face matching error: {e}")

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
        # Create initial case updates
        CaseUpdate.objects.create(
            case=instance,
            message="Thank you for submitting your case; we've received your information."
        )
        CaseUpdate.objects.create(
            case=instance,
            message=defaults['in_progress']
        )
        
        # Trigger AI facial recognition processing after transaction commits
        if instance.photo:
            print(f"🚀 Scheduling background AI processing for {instance.full_name} (ID: {instance.id})")
            
            def start_ai_processing():
                thread = threading.Thread(
                    target=process_face_matching_background, 
                    args=(instance.id,),
                    daemon=True
                )
                thread.start()
            
            # Wait for the transaction to commit before starting AI processing
            transaction.on_commit(start_ai_processing)
        else:
            print(f"⏭️ No photo provided for {instance.full_name}, skipping AI processing")
        
        return
    
    # Handle status changes for existing cases
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