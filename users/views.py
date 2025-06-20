from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, LoginSerializer, AdminUserSerializer, ProfileSerializer, ChangePasswordSerializer
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken
from firebase_admin import auth as firebase_auth
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime, timedelta
import uuid
import string
import random
import logging

logger = logging.getLogger(__name__)

def generate_random_password(length=12):
            characters = string.ascii_letters + string.digits + string.punctuation
            return ''.join(random.choice(characters) for _ in range(length))
        

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': ProfileSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    
    errors = serializer.errors
    
    if 'username' in errors:
        if any('unique' in str(error).lower() for error in errors['username']):
         return Response({
                "field": "username",
                "message": "Username is already taken."
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                "field": "username",
                "message": errors['username'][0] 
            }, status=status.HTTP_400_BAD_REQUEST)
    
    if 'email' in errors:
        if any('unique' in str(error).lower() for error in errors['email']):
            return Response({
                "field": "email",
                "message": "Email is already taken."
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                "field": "email",
                "message": errors['email'][0]  
            }, status=status.HTTP_400_BAD_REQUEST)
    
    if 'password' in errors:
        return Response({
            "field": "password",
            "message": errors['password'][0]  
        }, status=status.HTTP_400_BAD_REQUEST)
        
    if 'phone_number' in errors:
        return Response({
            "field": "phone_number",
            "message": errors['phone_number'][0]  
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if errors:
        first_field = list(errors.keys())[0]
        return Response({
            "field": first_field,
            "message": errors[first_field][0]  
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        "message": "An error occurred during registration."
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    print(request.data)
    serializer = LoginSerializer(data=request.data)
    
    # Return 400 for validation errors (empty fields, etc.)
    if not serializer.is_valid():
        return Response({
            'msg': 'Wrong password or username, please try again.',
            'code': '400'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    user = authenticate(username=username, password=password)
    
    # Success case
    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh), 
            'access': str(refresh.access_token),
            'user': ProfileSerializer(user).data,
            'code': '200'
        }, status=status.HTTP_200_OK)
    
    # Authentication failed - return 401
    else:
        return Response({
            'msg': 'Wrong password or username, please try again.',
            'code': '401'
        }, status=status.HTTP_401_UNAUTHORIZED)




@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def profile_user(request):
    user = request.user

    if request.method == 'GET':
        serializer = ProfileSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    elif request.method == 'PATCH':
        print(f"PATCH request data: {request.data}")
        serializer = ProfileSerializer(instance=user, data=request.data, partial=True, context={'request': request})
        
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Profile Updated!',
                    'user': ProfileSerializer(user, context={'request': request}).data
                }, status=status.HTTP_200_OK)
            except Exception as e:
                print(f"Error saving profile: {e}")
                return Response({
                    'success': False,
                    'message': f'Error updating profile: {str(e)}',
                    'user': ProfileSerializer(user, context={'request': request}).data
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            error_messages = {}
            for field, errors in serializer.errors.items():
                error_messages[field] = str(errors[0]) if errors else "Invalid data"
            
            print(f"Validation errors: {error_messages}")  
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': error_messages,
                'user': ProfileSerializer(user, context={'request': request}).data
            }, status=status.HTTP_400_BAD_REQUEST)
        


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
     serializer = ChangePasswordSerializer(data=request.data, context={'request' : request})
     serializer.is_valid(raise_exception=True)

     user = request.user
     user.set_password(serializer.validated_data['new_password'])
     user.save()

     return Response({"detail": "Password updated successfully"}, status=status.HTTP_200_OK)



@api_view(['GET', 'PATCH'])
@permission_classes([IsAdminUser])
def manage_users(request, pk=None):
    if pk is None:
         if request.method != 'GET':
              return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
         qs = User.objects.all()
         serializer= AdminUserSerializer(qs, many=True)
         return Response(serializer.data)
    
    user = get_object_or_404(User, pk=pk)

    if request.method == 'GET':
            serializer = AdminUserSerializer(user)
            return Response(serializer.data)
    
    elif request.method == 'PATCH':
         serializer = AdminUserSerializer(instance=user,data=request.data, partial=True)
         if serializer.is_valid():
               serializer.save()
               return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    


@api_view(['POST'])
@permission_classes([AllowAny])
def firebase_auth_view(request):
    try:
        id_token = request.data.get('id_token')
        provider = request.data.get('provider', 'firebase')
        email = request.data.get('email', '')
        name = request.data.get('name', '')
        phone_number = request.data.get('phone_number', '')
        photo_url = request.data.get('photo_url', '') 
        
        if not id_token:
            return Response({'error': 'No ID token provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate a random password
        import string
        import random
        def generate_random_password(length=12):
            characters = string.ascii_letters + string.digits + "!@#$%^&*()"
            return ''.join(random.choice(characters) for _ in range(length))
        
        if provider in ['google', 'facebook']:
            unique_id = email or f"{provider}_{id_token[:12]}"
            username = email.split('@')[0] if email else f"{provider}_user_{uuid.uuid4().hex[:8]}"
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1 
            
            try:
                if email:
                    user = User.objects.get(email=email)
                else:
                    user = User.objects.get(username=username)
            except User.DoesNotExist:
                # Use our custom function to generate a random password
                random_password = generate_random_password()
                user = User.objects.create_user(
                    username=username,
                    email=email or '',
                    password=random_password
                )
                if name:
                    name_parts = name.split(' ', 1)
                    user.first_name = name_parts[0]
                    if len(name_parts) > 1:
                        user.last_name = name_parts[1]
                
                # Add phone number from social auth if provided
                if phone_number:
                    user.phone_number = phone_number
                
                # Set default values for BasicUser fields
                user.language = User.LANGUAGE_ENGLISH
                user.theme = User.THEME_LIGHT
                user.location_permission = False
                user.role = User.ROLE_USER
                
                user.save()
                if photo_url:
                    try:
                        import requests
                        from django.core.files.base import ContentFile
                        import uuid
                        
                        response = requests.get(photo_url, timeout=10)
                        if response.status_code == 200:
                            # Generate a unique filename
                            file_extension = 'jpg'  # Default to jpg
                            if 'image/png' in response.headers.get('content-type', ''):
                                file_extension = 'png'
                            
                            filename = f"{user.username}_{uuid.uuid4().hex[:8]}.{file_extension}"
                            
                            # Save the profile photo
                            user.profile_photo.save(
                                filename,
                                ContentFile(response.content),
                                save=True
                            )
                            print(f"✅ Profile photo saved for user {user.username}")
                    except Exception as photo_error:
                        print(f"❌ Error saving profile photo for {user.username}: {photo_error}")
            
            # ✅ Also handle photo for EXISTING users (in case they didn't have one before)
            else:
                if photo_url and not user.profile_photo:
                    try:
                        import requests
                        from django.core.files.base import ContentFile
                        import uuid
                        
                        response = requests.get(photo_url, timeout=10)
                        if response.status_code == 200:
                            file_extension = 'jpg'
                            if 'image/png' in response.headers.get('content-type', ''):
                                file_extension = 'png'
                            
                            filename = f"{user.username}_{uuid.uuid4().hex[:8]}.{file_extension}"
                            
                            user.profile_photo.save(
                                filename,
                                ContentFile(response.content),
                                save=True
                            )
                            print(f"✅ Profile photo added to existing user {user.username}")
                    except Exception as photo_error:
                        print(f"❌ Error saving profile photo for existing user {user.username}: {photo_error}")

        else: 
            try: 
                decoded_token = firebase_auth.verify_id_token(id_token)
                firebase_uid = decoded_token['uid']
        
                email = decoded_token.get('email', '')
                name = decoded_token.get('name', '')
                phone = decoded_token.get('phone_number', '')
                
                phone_number = phone or phone_number
        
                username = email.split('@')[0] if email else f"user_{firebase_uid[:8]}"
        
                try:
                    if email:
                        user = User.objects.get(email=email)
                    else:
                        user = User.objects.get(username__startswith=f"user_{firebase_uid[:8]}")
                except User.DoesNotExist:
                    random_password = generate_random_password()
                    user = User.objects.create_user(
                        username=username,
                        email=email or '',
                        password=random_password,
                        phone_number=phone_number
                    )
            
                    if name:
                        name_parts = name.split(' ', 1)
                        user.first_name = name_parts[0]
                        if len(name_parts) > 1:
                            user.last_name = name_parts[1]
                    
                   
                    
                    user.save()
            except Exception as firebase_error:
                return Response({'error': f"Firebase verification error: {str(firebase_error)}"}, 
                              status=status.HTTP_400_BAD_REQUEST)
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone_number': user.phone_number or '',
                'profile_photo': request.build_absolute_uri(user.profile_photo.url) if user.profile_photo else None,
            },
            'expiry_time': (datetime.now() + timedelta(minutes=60)).isoformat(),
        })
    
    except Exception as e:
        print(f"Error in firebase_auth_view: {e}")
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def validate_fields(request):
    errors = {}
    
    username = request.data.get('username')
    if username and User.objects.filter(username=username).exists():
        errors['username'] = ['This username is already taken.']
    
    email = request.data.get('email')
    if email and User.objects.filter(email=email).exists():
        errors['email'] = ['This email is already registered.']
    
    phone_number = request.data.get('phone_number')
    if phone_number and User.objects.filter(phone_number=phone_number).exists():
        errors['phone_number'] = ['This phone number is already registered.']
    
    if errors:
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({'valid': True}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_account(request):
    username = request.data.get('username')
    
    try:
        user = User.objects.get(username=username)
        user.delete()
        return Response({"success": True}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"success": False, "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_fcm_token(request):
    fcm_token = request.data.get('fcm')
    if fcm_token:
        request.user.fcm = fcm_token
        request.user.save()
        return Response({'success': True})
    return Response({'error': 'FCM token required'}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_fcm_token(request):
    """
    Update FCM token for current user
    """
    fcm_token = request.data.get('fcm_token')
    
    if not fcm_token:
        return Response(
            {'error': 'FCM token is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    request.user.fcm = fcm_token
    request.user.save()
    
    return Response({
        'message': 'FCM token updated successfully',
        'user': request.user.username
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_fcm_token(request):
    """Remove user's FCM token (useful for logout)"""
    try:
        request.user.fcm = None
        request.user.save(update_fields=['fcm'])
        
        logger.info(f"FCM token removed for user {request.user.username}")
        return Response({'message': 'FCM token removed successfully'}, 
                       status=status.HTTP_200_OK)
                       
    except Exception as e:
        logger.error(f"Failed to remove FCM token for {request.user.username}: {str(e)}")
        return Response({'error': 'Failed to remove FCM token'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_fcm_status(request):
    """Check if user has FCM token registered"""
    has_token = bool(request.user.fcm)
    return Response({
        'has_fcm_token': has_token,
        'username': request.user.username
    })