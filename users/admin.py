from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from .models import BasicUser

admin.site.site_header = 'Admin Dashboard'
admin.site.index_title = 'Hey admin! Welcome Back :)'

class BasicUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = BasicUser
        fields = (
            'username', 'email', 'first_name', 'last_name',
            'phone_number', 'profile_photo', 'language', 'theme',
            'location_permission',
        )

@admin.register(BasicUser)
class AccountAdmin(UserAdmin):
    model = BasicUser
    add_form = BasicUserCreationForm

    list_display       = (
        'id',
        'username',
        'full_name',
        'email',
        'phone_number',
        'role',
        'is_active',
    )
    list_display_links = ('id', 'full_name')
    list_editable      = ('role',)
    list_filter        = ('role', 'is_active')
    search_fields      = ('username', 'email', 'phone_number')
    ordering           = ('username', 'first_name')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'first_name', 'last_name',
                'phone_number', 'profile_photo', 'language', 'theme',
                'location_permission', 'password1', 'password2',
            ),
        }),
    )

    def get_fieldsets(self, request, obj=None):
        if obj is not None:
            return [
                ('Permissions', {
                    'fields': ('is_active', 'role'),
                }),
            ]
        return self.add_fieldsets

    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return (
                'username', 'email', 'first_name', 'last_name',
                'phone_number', 'profile_photo', 'language', 'theme',
                'location_permission', 'last_login', 'date_joined'
            )
        return ()

    def full_name(self, obj):
        return obj.get_full_name()
    full_name.short_description = 'Full name'

    actions = [
        'set_role_to_admin',
        'set_role_to_user',
        'activate_users',
        'deactivate_users',
    ]

    @admin.action(description='Change selected users to Admin')
    def set_role_to_admin(self, request, queryset):
        updated = queryset.update(role=BasicUser.ROLE_ADMIN)
        self.message_user(request, f"{updated} account(s) set to Admin.")

    @admin.action(description='Change selected admins to User')
    def set_role_to_user(self, request, queryset):
        updated = queryset.update(role=BasicUser.ROLE_USER)
        self.message_user(request, f"{updated} account(s) set to User.")

    @admin.action(description='Activate selected user accounts')
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} user account(s) activated.")

    @admin.action(description='Deactivate selected user accounts')
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} user account(s) deactivated.")
