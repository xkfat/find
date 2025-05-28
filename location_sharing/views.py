from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

from missing.models import MissingPerson
from .signals import location_alert
from django.contrib.auth import get_user_model
from django.db.models import Q 
from .models import LocationRequest, LocationSharing, UserLocation
from .serializers import (
    LocationRequestSerializer, 
    LocationSharingSerializer, 
    UserLocationSerializer,
    UserSearchSerializer,
)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pending_requests(request):
    pending_requests = LocationRequest.objects.filter(
        receiver=request.user, 
        status='pending'
    )
    serializer = LocationRequestSerializer(pending_requests, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_location_request(request):
    identifier = request.data.get('identifier')
    receiver = find_user_by_identifier(identifier)
    if not receiver: 
        return Response(
            {"detail": "User not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )

    if LocationSharing.objects.filter(user=request.user, friend=receiver).exists():
        return Response(
            {"detail": "Already sharing location with this user"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    existing_request = LocationRequest.objects.filter(
        sender=request.user, 
        receiver=receiver,
        status='pending'
    ).first()
    
    if existing_request:
        return Response(
            {"detail": "Request already sent"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    data = {
        'sender': request.user.id, 
        'receiver': receiver.id
    }
    serializer = LocationRequestSerializer(data=data)
    
    if serializer.is_valid():
        serializer.save()
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
        LocationSharing.objects.create(
            user=request.user, 
            friend=location_request.sender,
            can_see_me=True  
        )
        LocationSharing.objects.create(
            user=location_request.sender, 
            friend=request.user,
            can_see_me=True  
        )
        
        UserLocation.objects.get_or_create(user=request.user)
        UserLocation.objects.get_or_create(user=location_request.sender)
        
        return Response({"detail": "Location sharing request accepted"})
    else:
        return Response({"detail": "Location sharing request declined"})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_friends(request):
    sharing = LocationSharing.objects.filter(user=request.user)
    serializer = LocationSharingSerializer(sharing, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_friend(request, friend_id):
    LocationSharing.objects.filter(user=request.user, friend_id=friend_id).delete()
    LocationSharing.objects.filter(user_id=friend_id, friend=request.user).delete()
    
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_alert(request, friend_id):
    friend = get_object_or_404(LocationSharing, user=request.user, friend_id=friend_id).friend
    location_alert.send(sender=request.user.__class__, instance=request.user, recipient=friend)
    return Response({"detail": "Location alert sent successfully"})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_friends_locations(request):
   
    
    print(f"DEBUG: Getting friends locations for user {request.user.id} ({request.user.username})")
    
    friends_sharing = LocationSharing.objects.filter(
        friend=request.user, 
        can_see_me=True      
    ).values_list('user', flat=True)
    
    print(f"DEBUG: Found {len(friends_sharing)} friends sharing with current user")
    
    recent_time = timezone.now() - timedelta(minutes=30)
    
    visible_locations = UserLocation.objects.filter(
        user__in=friends_sharing,
        is_sharing=True,  
        latitude__isnull=False, 
        longitude__isnull=False,
        last_updated__gte=recent_time 
    )
    
    print(f"DEBUG: Found {visible_locations.count()} recent visible locations")
    
    now = timezone.now()
    locations_data = []
    
    for location in visible_locations:
        time_diff = now - location.last_updated
        minutes_ago = int(time_diff.total_seconds() / 60)
        
        if minutes_ago <= 2:
            freshness = 'live'  
            display_text = 'Live'
        else:
            freshness = 'recent'  
            display_text = f"{minutes_ago}m ago"
        
        location_data = {
            'id': location.id,
            'user': location.user.id,
            'username': location.user.username,
            'latitude': str(location.latitude),
            'longitude': str(location.longitude),
            'last_updated': location.last_updated.isoformat(),
            'is_sharing': location.is_sharing,
            'minutes_ago': minutes_ago,
            'freshness': freshness,
            'display_text': display_text
        }
        
        locations_data.append(location_data)
        print(f"DEBUG: Location for {location.user.username}: {location.latitude}, {location.longitude} ({minutes_ago}m ago - {freshness})")
    
    return Response(locations_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_my_location(request):
    location, created = UserLocation.objects.get_or_create(user=request.user)
    
    location.is_sharing = True
    location.latitude = request.data.get('latitude')
    location.longitude = request.data.get('longitude')
    location.save()
    
    print(f"DEBUG: Updated location for {request.user.username}: {location.latitude}, {location.longitude}")
    
    serializer = UserLocationSerializer(location)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def toggle_global_sharing(request):
    location, created = UserLocation.objects.get_or_create(user=request.user)
    
    is_sharing = request.data.get('is_sharing')
    if is_sharing is None:
        return Response(
            {"detail": "is_sharing field is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    location.is_sharing = is_sharing
    location.save()
    
    return Response({
        "is_sharing": location.is_sharing,
        "detail": "Global location sharing updated successfully"
    })


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def toggle_friend_sharing(request, friend_id):
    sharing_relationship = get_object_or_404(
        LocationSharing, 
        user=request.user, 
        friend_id=friend_id
    )
    
    can_see_me = request.data.get('can_see_me')
    if can_see_me is None:
        return Response(
            {"detail": "can_see_me field is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    sharing_relationship.can_see_me = can_see_me
    sharing_relationship.save()
    
    return Response({
        "can_see_me": sharing_relationship.can_see_me,
        "detail": f"Sharing with friend {'enabled' if can_see_me else 'disabled'} successfully"
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_sharing_settings(request):
    location, created = UserLocation.objects.get_or_create(user=request.user)
    
    return Response({
        "is_sharing": location.is_sharing
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_users(request):
    query = request.GET.get('q', '').strip()
    
    if not query:
        return Response([], status=status.HTTP_200_OK)
    
    if len(query) < 1:
        return Response(
            {"detail": "Search query must be at least 1 character"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    excluded_user_ids = set()
    
    excluded_user_ids.add(request.user.id)
    
    pending_requests = LocationRequest.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user),
        status='pending'
    )
    for req in pending_requests:
        excluded_user_ids.add(req.sender.id)
        excluded_user_ids.add(req.receiver.id)
    
    existing_friends = LocationSharing.objects.filter(user=request.user)
    for friendship in existing_friends:
        excluded_user_ids.add(friendship.friend.id)
    
    User = get_user_model()
    users = User.objects.filter(
        Q(username__icontains=query) | 
        Q(first_name__icontains=query) | 
        Q(last_name__icontains=query)
    ).exclude(
        id__in=excluded_user_ids
    )[:20]  
    
    serializer = UserSearchSerializer(users, many=True, context={'request': request})
    return Response(serializer.data)


def find_user_by_identifier(identifier):
    User = get_user_model()
    user = User.objects.filter(username=identifier).first()
    if user:
        return user
        
    if hasattr(User, 'phone_number'):
        user = User.objects.filter(phone_number=identifier).first()
    return user


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_map_data(request):

    
    missing_persons = MissingPerson.objects.filter(status='active').values(
        'id', 'name', 'last_seen_lat', 'last_seen_lng', 'last_seen_date', 'case_number'
    )
    
    recent_time = timezone.now() - timedelta(minutes=15)
    friends_sharing = LocationSharing.objects.filter(
        friend=request.user,
        can_see_me=True
    ).values_list('user', flat=True)
    
    user_locations = UserLocation.objects.filter(
        user__in=friends_sharing,
        is_sharing=True,
        latitude__isnull=False,
        longitude__isnull=False,
        last_updated__gte=recent_time
    ).select_related('user')
    
    now = timezone.now()
    locations_list = []
    
    for location in user_locations:
        time_diff = now - location.last_updated
        minutes_ago = int(time_diff.total_seconds() / 60)
        
        if minutes_ago <= 2:
            freshness = 'live'
            display_text = 'Live'
        else:
            freshness = 'recent'
            display_text = f"{minutes_ago}m ago"
        
        location_data = {
            'username': location.user.username,
            'first_name': location.user.first_name or '',
            'last_name': location.user.last_name or '',
            'latitude': location.latitude,
            'longitude': location.longitude,
            'last_updated': location.last_updated.isoformat(),
            'minutes_ago': minutes_ago,
            'freshness': freshness,
            'display_text': display_text
        }
        locations_list.append(location_data)
    
    return Response({
        'missing_persons': list(missing_persons),
        'user_locations': locations_list,
        'last_updated': timezone.now()
    })