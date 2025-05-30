from firebase_admin import messaging
from firebase_admin import exceptions
import logging

logger = logging.getLogger(__name__)

def send_push_notification(title, body, fcm_token, data=None):
  
    if not fcm_token:
        logger.warning("No FCM token provided")
        return {'success': False, 'error': 'No FCM token'}
    
    try:
        message_data = {
            'notification': messaging.Notification(
                title=title,
                body=body,
            ),
            'token': fcm_token,
        }
        
        if data:
            message_data['data'] = {k: str(v) for k, v in data.items()}  
        
        message = messaging.Message(**message_data)
        
        response = messaging.send(message)
        logger.info(f"Push notification sent successfully: {response}")
        
        return {
            'success': True,
            'response': response,
            'message_id': response
        }
        
    except messaging.UnregisteredError:
        logger.warning(f"FCM token is unregistered: {fcm_token[:20]}...")
        return {
            'success': False,
            'error': 'Token unregistered',
            'should_remove_token': True
        }
        
    except messaging.SenderIdMismatchError:
        logger.warning(f"FCM sender ID mismatch: {fcm_token[:20]}...")
        return {
            'success': False,
            'error': 'Sender ID mismatch',
            'should_remove_token': True
        }
        
    except messaging.InvalidArgumentError as e:
        logger.error(f"Invalid FCM message: {str(e)}")
        return {
            'success': False,
            'error': f'Invalid message: {str(e)}'
        }
        
    except exceptions.FirebaseError as e:
        logger.error(f"Firebase error: {str(e)}")
        return {
            'success': False,
            'error': f'Firebase error: {str(e)}'
        }
        
    except Exception as e:
        logger.error(f"Unexpected error sending push notification: {str(e)}")
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }