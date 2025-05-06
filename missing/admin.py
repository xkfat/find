from django.contrib import admin, messages
from .models import MissingPerson, CaseUpdate


class CaseUpdates(admin.TabularInline):
   model = CaseUpdate
   extra = 0
   readonly_fields = ('timestamp', 'formatted_date')
   fields = ('message', 'timestamp', 'formatted_date')
   can_delete = False

@admin.register(MissingPerson)
class MissingPersonAdmin(admin.ModelAdmin):
    list_display = ('full_name','age','status', 'submission_status', 'reporter', 'date_reported', 'days_missing')
    search_fields = ('id', 'first_name', 'last_name', 'status', 'reporter__username', 'submission_status')
    list_filter = ('status','submission_status', 'gender', 'date_reported')
    inlines = [CaseUpdates]


    def get_readonly_fields(self, request, obj=None):
        if obj is None:  
            return ('date_reported',)
        return ('full_name', 'days_missing', 'date_reported')
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            ('Personal Information', {
                'fields': ('full_name', 'age', 'gender', 'photo')
            }),
            ('Missing Details', {
                'fields': ('last_seen_date', 'last_seen_location', 'latitude', 'longitude')
            }),
            ('Case Information', {
                'fields': ('description', 'status', 'reporter', 'submission_status')
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


    actions = ['change_to_found', 'change_to_under_investigation', 'change_to_missing',
               'change_submission_to_active', 
                'change_submission_to_in_in_progress',
                'change_submission_to_closed',
                'change_submission_to_rejected', 
 
 

               
               ]
    

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
    
    @admin.action(description='Change submission status to Active')
    def change_submission_to_active(self, request, queryset):
        updated = queryset.update(submission_status='active')
        messages.success(request, f"{updated} case(s) submission status set to Active.")

    @admin.action(description='Change submission status to In Progress')
    def change_submission_to_in_progress(self, request, queryset):
        updated = queryset.update(submission_status='in_progress')
        messages.success(request, f"{updated} case(s) submission status set to In Progress.")

    @admin.action(description='Change submission status to Closed')
    def change_submission_to_closed(self, request, queryset):
        updated = queryset.update(submission_status='closed')
        messages.success(request, f"{updated} case(s) submission status set to Closed.")

    @admin.action(description='Change submission status to Rejected')
    def change_submission_to_rejected(self, request, queryset):
        updated = queryset.update(submission_status='rejected')
        messages.success(request, f"{updated} case(s) submission status set to Rejected.")