from django.contrib import admin, messages
from .models import Report
from django.utils.html import format_html
from django.urls import reverse


@admin.action(description='Change selected reports to unverified')
def change_to_unverified(modeladmin, request, queryset):
    updated = queryset.update(report_status='unverified')
    messages.success(request, f"{updated} report(s) changed to unverified.")
    
@admin.action(description='Change selected reports to Verified')
def change_to_verified(modeladmin, request, queryset):
    updated = queryset.update(report_status='verified')
    messages.success(request, f"{updated} report(s) changed to verified.")

@admin.action(description='Change selected reports to False')
def change_to__false(modeladmin, request, queryset):
    updated = queryset.update(report_status='false')
    messages.success(request, f"{updated} report(s) changed to false.")
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'missing_person', 'report_status', 'view_note_link')
    readonly_fields = ('user', 'missing_person', 'date_submitted', 'report_status', 'note')
    list_filter = ('report_status', 'date_submitted')
    ordering = ('-date_submitted',)
    search_fields = ('note', 'user__username', 'missing_person__first_name')
    list_per_page = 5
    actions = [change_to_unverified, change_to_verified, change_to__false]
    date_hierarchy = 'date_submitted'

    def view_note_link(self, obj):
        url = reverse('admin:reports_report_change', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}">View Note</a>', url)
    view_note_link.short_description = 'Note'

    def has_add_permission(self, request):
        return False