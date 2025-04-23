from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import BasicUser



admin.site.site_header = 'Admin Dashboard '
admin.site.index_title = 'Hey admin! , Welcome Back :) '
@admin.register(BasicUser)
class CustomUserAdmin(UserAdmin):
    model = BasicUser

    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': (
                'phone_number', 'profile_photo', 
                'language', 'theme', 'location_permission',
            ),
        }),
    )
    list_display = (
        'username', 'email', 'phone_number', 'language', 'theme', 'is_staff', 'is_superuser'
    )