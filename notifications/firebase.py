from firebase_admin import messaging
from firebase_admin import exceptions
import logging

logger = logging.getLogger(__name__)

def send_push_notification(title, body, fcm_token, data=None):
    if not fcm_token:
        logger.warning("No FCM token provided")
        return {'success': False, 'error': 'No FCM token'}
    
    # 🔥 DEBUG: Log what we're trying to send
    logger.info(f"🔍 FIREBASE DEBUG: title='{title}', body='{body[:50]}...', token='{fcm_token[:20]}...'")
    
    try:
        message_data = {
            'token': fcm_token,
        }
        
        # 🔥 CRITICAL FIX: Always add notification part for push notifications
        if title is not None and title != "":
            message_data['notification'] = messaging.Notification(
                title=title,
                body=body,
            )
            logger.info(f"✅ Added notification with title: '{title}'")
        else:
            # For empty titles, still send notification but with body as title
            message_data['notification'] = messaging.Notification(
                title=body[:50],  # Use message as title if no title provided
                body=body,
            )
            logger.info(f"⚠️ Empty title - using message as title: '{body[:50]}'")
        
        if data:
            message_data['data'] = {k: str(v) for k, v in data.items()}  
            logger.info(f"📦 Added data payload: {list(data.keys())}")
        
        message = messaging.Message(**message_data)
        
        response = messaging.send(message)
        logger.info(f"✅ Push notification sent successfully: {response}")
        
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
        
    except exceptions.InvalidArgumentError as e:
        logger.error(f"Invalid FCM argument: {str(e)}")
        return {
            'success': False,
            'error': f'Invalid argument: {str(e)}'
        }
        
    except exceptions.FirebaseError as e:
        logger.error(f"Firebase error: {str(e)}")
        return {
            'success': False,
            'error': f'Firebase error: {str(e)}'
        }
        
    except ValueError as e:
        # Handle invalid message format
        logger.error(f"Invalid message format: {str(e)}")
        return {
            'success': False,
            'error': f'Invalid message: {str(e)}'
        }
        
    except Exception as e:
        logger.error(f"Unexpected error sending push notification: {str(e)}")
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }