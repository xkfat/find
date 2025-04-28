from django.contrib import admin, messages
from django.urls import path, reverse
from .models import Notification, BasicUser
from django.http import HttpResponse
from django.utils.html import format_html

@admin.register(Notification)
class NotificationsAdmin(admin.ModelAdmin):
    fields = ('user', 'message', 'is_read', 'date_created')
    list_display = ('user', 'date_created', 'view_message_button')
    list_filter = ('is_read', 'date_created', 'user__username')
    search_fields = ('user__username', 'message')


    actions = ['send_to_all_users']
    
    def send_to_all_users(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Please select only one notification to broadcast", messages.ERROR)
            return
            
        notification = queryset.first()
        users = BasicUser.objects.all().exclude(id=notification.user.id)
        count = 0
        
        for user in users:
            Notification.objects.create(
                user=user,
                message=notification.message
            )
            count += 1
            
        self.message_user(request, f"Successfully sent notification to {count} additional users", messages.SUCCESS)
    send_to_all_users.short_description = "Send selected notification to all users"
    

    def view_message_button(self, obj):
        url = reverse('admin:notifications_notification_change', args=[obj.pk])
        return format_html('<a class="button" href="{}">View</a>', url)
    
    view_message_button.short_description = 'Message'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:pk>/view-message/',
                self.admin_site.admin_view(self.view_message_view),
                name='view-message',
            ),
        ]
        return custom_urls + urls
    

    def view_message_view(self, request, pk):
        notification = Notification.objects.get(pk=pk)
        return HttpResponse(notification.message)
    


    def get_fields(self, request, obj=None):
        if obj:
            return ('user', 'message', 'is_read', 'date_created')
        return ('user', 'message')
    

    def get_readonly_fields(self, request, obj=None):
        if obj:  
         return ('user', 'message','is_read', 'date_created')
        return ()
    
    def has_add_permission(self, request):
        return True
    
    def has_view_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return True
    


    #Customize (might change later):
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Notification Details' 
        return super().change_view(request, object_id, form_url, extra_context)
    
    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if obj:  
            context.update({
                'show_save': False,
                'show_save_and_add_another': False,
                'show_save_and_continue': False,
                'show_history': False, 
            })
        return super().render_change_form(request, context, add, change, form_url, obj)
    
    def delete_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, object_id)
        extra_context = extra_context or {}

        extra_context['title'] = "Confirm Deletion of Notification"

        return super().delete_view(request, object_id, extra_context=extra_context)

    def get_deleted_objects(self, objs, request):
     obj = objs[0] 
     message_summary = f"{obj.message}"  

     return [], {"": message_summary}, set(), []
