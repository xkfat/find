from firebase_admin import messaging
from firebase_admin import exceptions

def send_push_notification(title, body, fcm):
    if not fcm:
        return
        
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=fcm,
    )
    try:
        response = messaging.send(message)
        return response
    except exceptions.FirebaseError as firebase_error:
        pass