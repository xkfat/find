from django.db import models
from django.conf import settings

class LocationRequest(models.Model):
    """Request from one user to another to establish location sharing"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined')
    ]
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sent_location_requests'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='received_location_requests'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('sender', 'receiver')
        verbose_name = 'Location Request'
        verbose_name_plural = 'Location Requests'
    
    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username} ({self.get_status_display()})"


class LocationSharing(models.Model):
    """Represents a bidirectional location sharing relationship between two users"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sharing_with'
    )
    friend = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='shared_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'friend')
        verbose_name = 'Location Sharing'
        verbose_name_plural = 'Location Sharing'
    
    def __str__(self):
        return f"{self.user.username} shares with {self.friend.username}"


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
    
    @property
    def has_location(self):
        return self.latitude is not None and self.longitude is not None


class SelectedFriend(models.Model):
    user_location = models.ForeignKey(
        UserLocation, 
        on_delete=models.CASCADE, 
        related_name='selected_friends'
    )
    friend = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('user_location', 'friend')
        verbose_name = 'Selected Friend'
        verbose_name_plural = 'Selected Friends'
    
    def __str__(self):
        return f"{self.user_location.user.username} selected {self.friend.username}"