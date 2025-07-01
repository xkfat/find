from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from .models import AIMatch

class ConfidenceLevelFilter(admin.SimpleListFilter):
    title = 'Confidence Level'
    parameter_name = 'confidence_level'

    def lookups(self, request, model_admin):
        return (
            ('high', 'High (90%+)'),
            ('medium', 'Medium (70-89%)'),
            ('low', 'Low (<70%)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'high':
            return queryset.filter(confidence_score__gte=90)
        elif self.value() == 'medium':
            return queryset.filter(confidence_score__gte=70, confidence_score__lt=90)
        elif self.value() == 'low':
            return queryset.filter(confidence_score__lt=70)
        return queryset

@admin.register(AIMatch)
class AIMatchAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'original_case_link', 'matched_case_link', 'confidence_score', 
        'confidence_level', 'status',
         # 'reviewed_by', 
         'processing_date'
    ]
    list_filter = [
        'status', 
        'processing_date', 
      #  'reviewed_by',
        ConfidenceLevelFilter,
    ]
    search_fields = [
        'original_case__first_name', 'original_case__last_name',
        'matched_case__first_name', 'matched_case__last_name'
    ]
    readonly_fields = [
        'processing_date', 'updated_at', 'confidence_level', 
        'original_case', 'matched_case', 'confidence_score',
        'face_distance', 
        #'algorithm_used'
    ]
    
    fieldsets = (
        ('Match Information', {
            'fields': ('original_case', 'matched_case', 'confidence_score', 'confidence_level')
        }),
       
       
        ('Metadata', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        })
    )
    
    actions = ['confirm_matches', 'reject_matches']
    
    def original_case_link(self, obj):
        url = reverse('admin:missing_missingperson_change', args=[obj.original_case.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.original_case.full_name
        )
    original_case_link.short_description = 'Original Case'
    
    def matched_case_link(self, obj):
        url = reverse('admin:missing_missingperson_change', args=[obj.matched_case.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.matched_case.full_name
        )
    matched_case_link.short_description = 'Matched Case'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'original_case', 'matched_case', 
            #'reviewed_by'
        )
    
    def has_add_permission(self, request):
        return False
    
    def add_view(self, request, form_url='', extra_context=None):
        messages.warning(
            request, 
            "AI Matches are created automatically when missing persons are added. "
            "You cannot create them manually."
        )
        return HttpResponseRedirect(reverse('admin:ai_matches_aimatch_changelist'))
    
    @admin.action(description='Confirm selected matches')
    def confirm_matches(self, request, queryset):
        pending_matches = queryset.filter(status='pending')
        count = 0
        for match in pending_matches:
            match.confirm_match(request.user, "Bulk confirmed via admin")
            count += 1
        
        if count > 0:
            self.message_user(request, f"{count} matches confirmed successfully.")
        else:
            self.message_user(request, "No pending matches were selected.")
    
    @admin.action(description='Reject selected matches')
    def reject_matches(self, request, queryset):
        pending_matches = queryset.filter(status='pending')
        count = 0
        for match in pending_matches:
            match.reject_match(request.user, "Bulk rejected via admin")
            count += 1
        
        if count > 0:
            self.message_user(request, f"{count} matches rejected successfully.")
        else:
            self.message_user(request, "No pending matches were selected.")
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  
            return self.readonly_fields + ['created_at']
        return self.readonly_fields