# location_sharing/models.py
from django.db import models
from django.conf import settings

class LocationRequest(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_location_requests')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_location_requests')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('sender', 'receiver')
        verbose_name = 'Location Request'
        verbose_name_plural = 'Location Requests'
    
    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username}"

class LocationSharing(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sharing_with')
    shared_with = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shared_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'shared_with')
        verbose_name = 'Location Sharing'
        verbose_name_plural = 'Location Sharing'
    
    def __str__(self):
        return f"{self.user.username} shares with {self.shared_with.username}"

class UserLocation(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    is_sharing = models.BooleanField(default=False)
    share_with_all_friends = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'User Location'
        verbose_name_plural = 'User Locations'
    
    def __str__(self):
        return f"{self.user.username}'s location"
    
class SelectedFriends(models.Model):
    user_location = models.ForeignKey(UserLocation, on_delete=models.CASCADE, related_name='selected_friends')
    friend = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('user_location', 'friend')
    
    def __str__(self):
        return f"{self.user_location.user.username} selected {self.friend.username}"