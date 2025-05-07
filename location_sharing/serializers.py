from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import LocationRequest, LocationSharing, UserLocation, SelectedFriend

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Basic user information serializer"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        extra_kwargs = {'email': {'read_only': True}}


class LocationRequestSerializer(serializers.ModelSerializer):
    """Serializer for location sharing requests"""
    sender_details = UserSerializer(source='sender', read_only=True)
    receiver_details = UserSerializer(source='receiver', read_only=True)
    
    class Meta:
        model = LocationRequest
        fields = [
            'id', 'sender', 'receiver', 'status', 'created_at',
            'sender_details', 'receiver_details'
        ]
        read_only_fields = ['created_at', 'status']


class LocationSharingSerializer(serializers.ModelSerializer):
    """Serializer for location sharing relationships"""
    friend_details = UserSerializer(source='friend', read_only=True)
    
    class Meta:
        model = LocationSharing
        fields = ['id', 'user', 'friend', 'created_at', 'friend_details']
        read_only_fields = ['user', 'created_at']


class UserLocationSerializer(serializers.ModelSerializer):
    """Serializer for user location data"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserLocation
        fields = [
            'id', 'user', 'username', 'latitude', 'longitude',
            'last_updated', 'is_sharing', 'share_with_all_friends'
        ]
        read_only_fields = ['user', 'last_updated']


class SelectedFriendSerializer(serializers.ModelSerializer):
    """Serializer for selected friends (limited sharing)"""
    friend_details = UserSerializer(source='friend', read_only=True)
    
    class Meta:
        model = SelectedFriend
        fields = ['id', 'user_location', 'friend', 'friend_details']
        read_only_fields = ['user_location']