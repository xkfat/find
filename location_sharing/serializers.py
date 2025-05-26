from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.conf import settings
from .models import LocationRequest, LocationSharing, UserLocation, SelectedFriend

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Basic user information serializer"""
    profile_photo = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'profile_photo', 'display_name']
        extra_kwargs = {'email': {'read_only': True}}
    
    def get_profile_photo(self, obj):
        """Return full URL for profile photo or None"""
        if obj.profile_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_photo.url)
            else:
                # Fallback if no request context
                return f"{settings.MEDIA_URL}{obj.profile_photo}"
        return None
    
    def get_display_name(self, obj):
        """Return full name if available, otherwise username"""
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        elif obj.first_name:
            return obj.first_name
        return obj.username


class UserSearchSerializer(serializers.ModelSerializer):
    """Serializer for user search results"""
    profile_photo = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'profile_photo', 'display_name', 'full_name']
    
    def get_profile_photo(self, obj):
        """Return full URL for profile photo or None"""
        if hasattr(obj, 'profile_photo') and obj.profile_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_photo.url)
            else:
                return f"{settings.MEDIA_URL}{obj.profile_photo}"
        return None
    
    def get_display_name(self, obj):
        """Return full name if available, otherwise username"""
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        elif obj.first_name:
            return obj.first_name
        return obj.username
    
    def get_full_name(self, obj):
        """Return full name"""
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        elif obj.first_name:
            return obj.first_name
        return ""


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
    
    def to_representation(self, instance):
        """Include request context for nested serializers"""
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request:
            data['sender_details'] = UserSerializer(instance.sender, context={'request': request}).data
            data['receiver_details'] = UserSerializer(instance.receiver, context={'request': request}).data
        return data


class LocationSharingSerializer(serializers.ModelSerializer):
    """Serializer for location sharing relationships"""
    friend_details = UserSerializer(source='friend', read_only=True)
    
    class Meta:
        model = LocationSharing
        fields = ['id', 'user', 'friend', 'created_at', 'friend_details']
        read_only_fields = ['user', 'created_at']
    
    def to_representation(self, instance):
        """Include request context for nested serializers"""
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request:
            data['friend_details'] = UserSerializer(instance.friend, context={'request': request}).data
        return data


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
    friend_details = UserSerializer(source='friend', read_only=True)
    
    class Meta:
        model = SelectedFriend
        fields = ['id', 'user_location', 'friend', 'friend_details']
        read_only_fields = ['user_location']
    
    def to_representation(self, instance):
        """Include request context for nested serializers"""
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request:
            data['friend_details'] = UserSerializer(instance.friend, context={'request': request}).data
        return data