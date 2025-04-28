from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import BasicUser

admin.site.site_header  = 'Admin Dashboard'
admin.site.index_title  = 'Hey admin! Welcome Back :)'

@admin.register(BasicUser)
class AccountAdmin(UserAdmin):
    model = BasicUser

    list_display = (
        'username','first_name', 'last_name', 'email', 'phone_number',
        'role', 'is_active'
    )
    list_filter = (
        'role', 'is_active',
    )
    list_editable = ('role',)
    search_fields = (
        'username', 'email', 'phone_number'
    )
    ordering = ('username', 'first_name')

    fieldsets = (
        (None, {
            'fields': (
                'username', 'email',
                'first_name', 'last_name',
            ),
        }),
        ('Custom Fields', {
            'fields': (
                'phone_number', 'profile_photo',
                'language', 'theme', 'location_permission',
            ),
        }),
        ('Permissions', {
            'fields': (
                'is_active', 'role',
            ),
        }),
    )

    readonly_fields = (
      'email',
        'first_name', 'last_name',
        'phone_number', 'profile_photo',
        'language', 'theme', 'location_permission',
        
    )

    actions = [
        'set_role_to_admin',
        'set_role_to_user',
        'activate_users',
        'deactivate_users',
    ]

    @admin.action(description='Change selected users to admins')
    def set_role_to_admin(self, request, queryset):
        updated = queryset.update(role=BasicUser.ROLE_ADMIN)
        self.message_user(
            request,
            f"{updated} accounts(s) set to admin."
        )
    @admin.action(description='Change selected admins to users')
    def set_role_to_user(self, request, queryset):
        updated = queryset.update(role=BasicUser.ROLE_USER)
        self.message_user(
            request,
            f"{updated} accounts(s) set to User."
        )

    @admin.action(description='Activate selected user accounts')
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f"{updated} user account(s) activated."
        )

    @admin.action(description='Deactivate selected user accounts')
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f"{updated} user account(s) deactivated."
        )
