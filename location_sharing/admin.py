from django.contrib import admin
from .models import LocationRequest, LocationSharing, UserLocation, SelectedFriends

@admin.register(LocationRequest)
class LocationRequestAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'created_at']
    list_filter = ['created_at']
    search_fields = ['sender__username', 'receiver__username']

@admin.register(LocationSharing)
class LocationSharingAdmin(admin.ModelAdmin):
    list_display = ['user', 'shared_with', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'shared_with__username']
    
    def get_queryset(self, request):
        return super().get_queryset(request)

@admin.register(UserLocation)
class UserLocationAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_sharing', 'latitude', 'longitude', 'last_updated']
    list_filter = ['is_sharing', 'share_with_all_friends']
    search_fields = ['user__username']
    
    fieldsets = (
        (None, {
            'fields': ('user',)
        }),
        ('Location Data', {
            'fields': ('latitude', 'longitude', 'last_updated')
        }),
        ('Sharing Settings', {
            'fields': ('is_sharing', 'share_with_all_friends')
        }),
    )
    

@admin.register(SelectedFriends)
class SelectedFriendAdmin(admin.ModelAdmin):
    list_display = ['user_location', 'friend']
    search_fields = ['user_location__user__username', 'friend__username']