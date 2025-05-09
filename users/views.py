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
    return Response({'detail': 'Wrong username or password! please try again.'}, status=status.HTTP_401_UNAUTHORIZED)


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
    
