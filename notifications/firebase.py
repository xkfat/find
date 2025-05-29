# notifications/firebase.py
from firebase_admin import messaging
from firebase_admin import exceptions
import logging

logger = logging.getLogger(__name__)

def send_push_notification(title, body, fcm_token, data=None):
    """
    Send push notification via Firebase Cloud Messaging
    
    Args:
        title (str): Notification title
        body (str): Notification body
        fcm_token (str): FCM token of the target device
        data (dict): Additional data to send with notification
    
    Returns:
        dict: Result with success status and details
    """
    if not fcm_token:
        logger.warning("No FCM token provided")
        return {'success': False, 'error': 'No FCM token'}
    
    try:
        # Build message
        message_data = {
            'notification': messaging.Notification(
                title=title,
                body=body,
            ),
            'token': fcm_token,
        }
        
        # Add custom data if provided
        if data:
            message_data['data'] = {k: str(v) for k, v in data.items()}  # FCM data must be strings
        
        message = messaging.Message(**message_data)
        
        # Send message
        response = messaging.send(message)
        logger.info(f"Push notification sent successfully: {response}")
        
        return {
            'success': True,
            'response': response,
            'message_id': response
        }
        
    except messaging.UnregisteredError:
        # Token is invalid/unregistered
        logger.warning(f"FCM token is unregistered: {fcm_token[:20]}...")
        return {
            'success': False,
            'error': 'Token unregistered',
            'should_remove_token': True
        }
        
    except messaging.SenderIdMismatchError:
        # Token belongs to different sender
        logger.warning(f"FCM sender ID mismatch: {fcm_token[:20]}...")
        return {
            'success': False,
            'error': 'Sender ID mismatch',
            'should_remove_token': True
        }
        
    except messaging.InvalidArgumentError as e:
        # Invalid message format
        logger.error(f"Invalid FCM message: {str(e)}")
        return {
            'success': False,
            'error': f'Invalid message: {str(e)}'
        }
        
    except exceptions.FirebaseError as e:
        # Other Firebase errors
        logger.error(f"Firebase error: {str(e)}")
        return {
            'success': False,
            'error': f'Firebase error: {str(e)}'
        }
        
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error sending push notification: {str(e)}")
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }