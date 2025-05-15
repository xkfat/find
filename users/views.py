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
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
       return Response({'detail': 'Wrong password or username, please try again.'}, status=status.HTTP_401_UNAUTHORIZED)
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    user = authenticate(username=username, password=password)

    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh' : str(refresh), 
            'access' : str(refresh.access_token),
            'user': ProfileSerializer(user).data
        }, status=status.HTTP_200_OK)






@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def profile_user(request):
    user = request.user

    if request.method == 'GET':
        serializer = ProfileSerializer(user , context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    elif request.method == 'PATCH':
        serializer = ProfileSerializer(instance=user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
               serializer.save()
               return Response({
                 'message': 'Profile Updated!',
                 'user': ProfileSerializer(user, context={'request':request}).data
        }, status= status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        if not id_token:
            return Response({'error': 'No ID token provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        decoded_token = firebase_auth.verify_id_token(id_token)
        firebase_uid = decoded_token['uid']
        
        email = decoded_token.get('email', '')
        name = decoded_token.get('name', '')
        phone = decoded_token.get('phone_number', '')
        
        username = email.split('@')[0] if email else f"user_{firebase_uid[:8]}"
        
        try:
            if email:
                user = User.objects.get(email=email)
            else:
                user = User.objects.get(username__startswith=f"user_{firebase_uid[:8]}")
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=username,
                email=email or '',
                password=User.objects.make_random_password() 
            )
            
            if name:
                name_parts = name.split(' ', 1)
                user.first_name = name_parts[0]
                if len(name_parts) > 1:
                    user.last_name = name_parts[1]
                user.save()
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': {
                'id': User.id,
                'username': User.username,
                'email': User.email,
                'first_name': User.first_name,
                'last_name': User.last_name,
                'phone_number': phone,
            },
            'expiry_time': (datetime.now() + timedelta(minutes=60)).isoformat(),
        })
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)