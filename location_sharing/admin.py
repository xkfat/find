from django.contrib import admin
from .models import LocationRequest, LocationSharing, UserLocation

@admin.register(LocationRequest)
class LocationRequestAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('sender__username', 'receiver__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
    actions = ['accept_requests', 'decline_requests']
    
    def accept_requests(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='accepted')
        self.message_user(request, f'{updated} requests were accepted.')
    accept_requests.short_description = 'Accept selected requests'
    
    def decline_requests(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='declined')
        self.message_user(request, f'{updated} requests were declined.')
    decline_requests.short_description = 'Decline selected requests'


@admin.register(LocationSharing)
class LocationSharingAdmin(admin.ModelAdmin):
    list_display = ('user', 'friend', 'can_see_me', 'created_at')
    list_filter = ('can_see_me', 'created_at')
    search_fields = ('user__username', 'friend__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
    list_editable = ('can_see_me',)


@admin.register(UserLocation)
class UserLocationAdmin(admin.ModelAdmin):
    list_display = ('user', 'latitude', 'longitude', 'last_updated', 'is_sharing')
    list_filter = ('is_sharing', 'last_updated')
    search_fields = ('user__username',)
    readonly_fields = ('last_updated',)
    date_hierarchy = 'last_updated'
    list_editable = ('is_sharing',)
    fieldsets = (
        (None, {
            'fields': ('user',)
        }),
        ('Location Data', {
            'fields': ('latitude', 'longitude', 'last_updated')
        }),
        ('Sharing Settings', {
            'fields': ('is_sharing',)
        }),
    )