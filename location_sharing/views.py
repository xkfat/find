# location_sharing/views.py
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.apps import apps

from .models import LocationRequest, LocationSharing, UserLocation, SelectedFriends
from .serializers import (
    LocationRequestSerializer, 
    LocationSharingSerializer, 
    UserLocationSerializer,
    SelectedFriendSerializer
)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_location_requests(request):
    """Get pending location requests"""
    requests = LocationRequest.objects.filter(receiver=request.user)
    serializer = LocationRequestSerializer(requests, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_location_request(request):
    """Send location request to another user"""
    receiver_id = request.data.get('receiver')
    
    # Check if already friends
    if LocationSharing.objects.filter(user=request.user, shared_with_id=receiver_id).exists():
        return Response({"detail": "Already sharing location with this user"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if request already exists
    if LocationRequest.objects.filter(sender=request.user, receiver_id=receiver_id).exists():
        return Response({"detail": "Request already sent"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Create request
    data = {'sender': request.user.id, 'receiver': receiver_id}
    serializer = LocationRequestSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        
        # Send notification
        Notification = apps.get_model('notifications', 'Notification')
        Notification.objects.create(
            user_id=receiver_id,
            type='location_request',
            message=f"{request.user.username} wants to share location with you",
            related_id=serializer.instance.id
        )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_location_request(request, request_id):
    """Accept location sharing request"""
    location_request = get_object_or_404(LocationRequest, id=request_id, receiver=request.user)
    
    # Create two-way location sharing
    LocationSharing.objects.create(user=request.user, shared_with=location_request.sender)
    LocationSharing.objects.create(user=location_request.sender, shared_with=request.user)
    
    # Delete the request
    location_request.delete()
    
    # Notify sender
    Notification = apps.get_model('notifications', 'Notification')
    Notification.objects.create(
        user=location_request.sender,
        type='location_accepted',
        message=f"{request.user.username} accepted your location sharing request"
    )
    
    return Response({"detail": "Location sharing accepted"})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def decline_location_request(request, request_id):
    """Decline location sharing request"""
    location_request = get_object_or_404(LocationRequest, id=request_id, receiver=request.user)
    location_request.delete()
    return Response({"detail": "Location sharing declined"})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_sharing_friends(request):
    """Get list of friends you're sharing location with"""
    sharing = LocationSharing.objects.filter(user=request.user)
    serializer = LocationSharingSerializer(sharing, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_alert(request, user_id):
    """Send location alert to a friend"""
    # Check if sharing relationship exists
    get_object_or_404(LocationSharing, user=request.user, shared_with_id=user_id)
    
    # Send notification
    Notification = apps.get_model('notifications', 'Notification')
    Notification.objects.create(
        user_id=user_id,
        type='location_alert',
        message=f"{request.user.username} sent you a location alert",
        related_id=request.user.id
    )
    
    return Response({"detail": "Alert sent"})

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_friend(request, user_id):
    """Remove location sharing with a friend"""
    # Remove both directions of location sharing
    LocationSharing.objects.filter(user=request.user, shared_with_id=user_id).delete()
    LocationSharing.objects.filter(user_id=user_id, shared_with=request.user).delete()
    
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_friends_locations(request):
    """Get locations of friends sharing with you"""
    # Get users sharing with you
    sharing_users = LocationSharing.objects.filter(
        shared_with=request.user
    ).values_list('user', flat=True)
    
    # Get your location settings
    user_location, created = UserLocation.objects.get_or_create(user=request.user)
    
    # Check who can see you based on settings
    visible_locations = UserLocation.objects.filter(
        user__in=sharing_users,
        is_sharing=True  # Only if they have sharing enabled
    )
    
    # Filter for selected friends if they're not sharing with all
    non_all_sharing = visible_locations.filter(share_with_all_friends=False)
    for loc in non_all_sharing:
        # Check if you're a selected friend
        if not SelectedFriends.objects.filter(user_location=loc, friend=request.user).exists():
            visible_locations = visible_locations.exclude(id=loc.id)
    
    serializer = UserLocationSerializer(visible_locations, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_my_location(request):
    """Update your current location"""
    location, created = UserLocation.objects.get_or_create(user=request.user)
    
    serializer = UserLocationSerializer(location, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_sharing_settings(request):
    """Update location sharing settings"""
    location, created = UserLocation.objects.get_or_create(user=request.user)
    
    is_sharing = request.data.get('is_sharing')
    share_with_all_friends = request.data.get('share_with_all_friends')
    
    if is_sharing is not None:
        location.is_sharing = is_sharing
    if share_with_all_friends is not None:
        location.share_with_all_friends = share_with_all_friends
    
    location.save()
    
    # Handle selected friends if not sharing with all
    if not location.share_with_all_friends and 'selected_friends' in request.data:
        # Clear current selections
        SelectedFriends.objects.filter(user_location=location).delete()
        
        # Add new selections
        selected_friends = request.data.get('selected_friends', [])
        for friend_id in selected_friends:
            SelectedFriends.objects.create(user_location=location, friend_id=friend_id)
    
    return Response({
        "is_sharing": location.is_sharing,
        "share_with_all_friends": location.share_with_all_friends
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_selected_friends(request):
    """Get friends selected for limited sharing"""
    location, created = UserLocation.objects.get_or_create(user=request.user)
    selected = SelectedFriends.objects.filter(user_location=location)
    serializer = SelectedFriendSerializer(selected, many=True)
    return Response(serializer.data)