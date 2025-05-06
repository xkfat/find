# location_sharing/serializers.py
from rest_framework import serializers
from .models import LocationRequest, LocationSharing, UserLocation, SelectedFriends
from django.contrib.auth import get_user_model

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']
        # Add profile_image field if your User model has it

class LocationRequestSerializer(serializers.ModelSerializer):
    sender_details = UserBasicSerializer(source='sender', read_only=True)
    receiver_details = UserBasicSerializer(source='receiver', read_only=True)
    
    class Meta:
        model = LocationRequest
        fields = ['id', 'sender', 'receiver', 'sender_details', 'receiver_details', 'created_at']
        read_only_fields = ['created_at']

class LocationSharingSerializer(serializers.ModelSerializer):
    shared_with_details = UserBasicSerializer(source='shared_with', read_only=True)
    
    class Meta:
        model = LocationSharing
        fields = ['id', 'user', 'shared_with', 'shared_with_details', 'created_at']
        read_only_fields = ['user', 'created_at']

class UserLocationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserLocation
        fields = ['id', 'user', 'username', 'latitude', 'longitude', 'last_updated', 'is_sharing', 'share_with_all_friends']
        read_only_fields = ['user', 'last_updated']

class SelectedFriendSerializer(serializers.ModelSerializer):
    friend_details = UserBasicSerializer(source='friend', read_only=True)
    
    class Meta:
        model = SelectedFriends
        fields = ['id', 'user_location', 'friend', 'friend_details']
        read_only_fields = ['user_location']