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
    # NEW: Individual sharing control per friend
    can_see_me = models.BooleanField(default=True)  # Whether this friend can see my location
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'friend')
        verbose_name = 'Location Sharing'
        verbose_name_plural = 'Location Sharing'
    
    def __str__(self):
        visibility = "can see" if self.can_see_me else "cannot see"
        return f"{self.friend.username} {visibility} {self.user.username}'s location"


class UserLocation(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    # Simplified: Only one boolean for global sharing
    is_sharing = models.BooleanField(default=False)  # Global location sharing toggle
    
    class Meta:
        verbose_name = 'User Location'
        verbose_name_plural = 'User Locations'
    
    def __str__(self):
        return f"{self.user.username}'s location ({'sharing' if self.is_sharing else 'not sharing'})"
    
    @property
    def has_location(self):
        return self.latitude is not None and self.longitude is not None