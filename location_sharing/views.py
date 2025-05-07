from django.shortcuts import get_object_or_404
from django.apps import apps
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import LocationRequest, LocationSharing, UserLocation, SelectedFriend
from .serializers import (
    LocationRequestSerializer, 
    LocationSharingSerializer, 
    UserLocationSerializer,
    SelectedFriendSerializer
)

# Location Request Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pending_requests(request):
    """Get all pending location sharing requests for the current user"""
    pending_requests = LocationRequest.objects.filter(
        receiver=request.user, 
        status='pending'
    )
    serializer = LocationRequestSerializer(pending_requests, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_location_request(request):
    receiver_id = request.data.get('receiver')
    
    if LocationSharing.objects.filter(user=request.user, friend_id=receiver_id).exists():
        return Response(
            {"detail": "Already sharing location with this user"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    existing_request = LocationRequest.objects.filter(
        sender=request.user, 
        receiver_id=receiver_id,
        status='pending'
    ).first()
    
    if existing_request:
        return Response(
            {"detail": "Request already sent"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    data = {
        'sender': request.user.id, 
        'receiver': receiver_id
    }
    serializer = LocationRequestSerializer(data=data)
    
    if serializer.is_valid():
        location_request = serializer.save()
        
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def respond_to_request(request, request_id):
    location_request = get_object_or_404(
        LocationRequest, 
        id=request_id, 
        receiver=request.user,
        status='pending'
    )
    
    response = request.data.get('response')
    if response not in ['accept', 'decline']:
        return Response(
            {"detail": "Invalid response. Use 'accept' or 'decline'"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    location_request.status = 'accepted' if response == 'accept' else 'declined'
    location_request.save()
    
    if response == 'accept':
        # Create bidirectional location sharing
        LocationSharing.objects.create(user=request.user, friend=location_request.sender)
        LocationSharing.objects.create(user=location_request.sender, friend=request.user)
        
        # Ensure both users have UserLocation objects
        UserLocation.objects.get_or_create(user=request.user)
        UserLocation.objects.get_or_create(user=location_request.sender)
        
     
        
        return Response({"detail": "Location sharing request accepted"})
    else:
        return Response({"detail": "Location sharing request declined"})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_friends(request):
    sharing = LocationSharing.objects.filter(user=request.user)
    serializer = LocationSharingSerializer(sharing, many=True)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_friend(request, friend_id):
    """Stop sharing location with a specific friend (bidirectional)"""
    # Check if relationship exists
    sharing = get_object_or_404(LocationSharing, user=request.user, friend_id=friend_id)
    
    # Remove both directions of location sharing
    LocationSharing.objects.filter(user=request.user, friend_id=friend_id).delete()
    LocationSharing.objects.filter(user_id=friend_id, friend=request.user).delete()
    
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_alert(request, friend_id):
    friend = get_object_or_404(LocationSharing, user=request.user, friend_id=friend_id).friend
    send_location_alert(sender=request.user, recipient=friend)

  
    return Response({"detail": "Location alert sent successfully"})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_friends_locations(request):
    friends_sharing = LocationSharing.objects.filter(
        friend=request.user
    ).values_list('user', flat=True)
    
    # Get the current user's location settings
    user_location, _ = UserLocation.objects.get_or_create(user=request.user)
    
    # Filter for friends who are actively sharing
    visible_locations = UserLocation.objects.filter(
        user__in=friends_sharing,
        is_sharing=True,  # Only if sharing is enabled
        latitude__isnull=False,  # Must have location data
        longitude__isnull=False
    )
    
    # Filter for selected friends if not sharing with all
    limited_sharing_users = visible_locations.filter(share_with_all_friends=False)
    for loc in limited_sharing_users:
        # Check if current user is a selected friend
        if not SelectedFriend.objects.filter(user_location=loc, friend=request.user).exists():
            visible_locations = visible_locations.exclude(id=loc.id)
    
    serializer = UserLocationSerializer(visible_locations, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_my_location(request):
    """Update current user's location"""
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
    
    # Update sharing settings
    is_sharing = request.data.get('is_sharing')
    share_with_all_friends = request.data.get('share_with_all_friends')
    
    if is_sharing is not None:
        location.is_sharing = is_sharing
    if share_with_all_friends is not None:
        location.share_with_all_friends = share_with_all_friends
    
    location.save()
    
    # Handle selected friends if not sharing with all
    if 'selected_friends' in request.data:
        # Clear current selections
        SelectedFriend.objects.filter(user_location=location).delete()
        
        # Add new selections
        selected_friends = request.data.get('selected_friends', [])
        for friend_id in selected_friends:
            # Verify this is actually a friend
            if LocationSharing.objects.filter(user=request.user, friend_id=friend_id).exists():
                SelectedFriend.objects.create(user_location=location, friend_id=friend_id)
    
    return Response({
        "is_sharing": location.is_sharing,
        "share_with_all_friends": location.share_with_all_friends
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_selected_friends(request):
    """Get friends selected for limited sharing"""
    location, created = UserLocation.objects.get_or_create(user=request.user)
    selected = SelectedFriend.objects.filter(user_location=location)
    serializer = SelectedFriendSerializer(selected, many=True)
    return Response(serializer.data)