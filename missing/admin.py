from django.contrib import admin, messages
from .models import MissingPerson


@admin.register(MissingPerson)
class MissingPersonAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name','age','status', 'reporter', 'date_reported', 'days_missing')
    search_fields = ('first_name', 'last_name', 'status', 'reporter__username',)
    list_filter = ('status', 'gender', 'date_reported')


    def get_readonly_fields(self, request, obj=None):
        if obj is None:  
            return ('date_reported',)
        return ('full_name', 'days_missing', 'date_reported')
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            ('Personal Information', {
                'fields': ('first_name', 'last_name', 'age', 'gender', 'photo')
            }),
            ('Missing Details', {
                'fields': ('last_seen_date', 'last_seen_location', 'latitude', 'longitude')
            }),
            ('Case Information', {
                'fields': ('description', 'status', 'reporter')
            }),
        ]
        
        if obj is not None:  
            fieldsets.append(
                ('Additional Information', {
                    'fields': self.get_readonly_fields(request, obj),
                    'classes': ('collapse',)
                })
            )
            
        return fieldsets


    actions = ['change_to_found', 'change_to_under_investigation', 'change_to_missing']
    

    @admin.action(description='Change selected cases to found')
    def change_to_found(modeladmin, request, queryset):
       updated = queryset.update(status='found')
       messages.success(request, f"{updated} case status to found.")
    @admin.action(description='Change selected cases to searching')
    def change_to_under_investigation(modeladmin, request, queryset):
      updated = queryset.update(status='missing')
      messages.success(request, f"{updated} case status to missing.")

    @admin.action(description='Change selected cases to under investigation')
    def change_to_searching(modeladmin, request, queryset):
     updated = queryset.update(status='Investigating')
     messages.success(request, f"{updated} case status to under investigation.")
