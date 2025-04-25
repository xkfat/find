from django.contrib import admin, messages
from .models import MissingPerson


@admin.register(MissingPerson)
class MissingPersonAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'status', 'reporter', 'date_reported')
    search_fields = ('first_name', 'last_name', 'status', 'reporter__username',)
    list_filter = ('status', 'gender', 'date_reported', 'id')
    actions = ['change_to_found', 'change_to_under_investigation', 'change_to_searching']
    
    @admin.action(description='Change selected cases to found')
    def change_to_found(modeladmin, request, queryset):
       updated = queryset.update(status='found')
       messages.success(request, f"{updated} case status to found.")
    @admin.action(description='Change selected cases to searching')
    def change_to_under_investigation(modeladmin, request, queryset):
      updated = queryset.update(status='searching')
      messages.success(request, f"{updated} case status to searching.")

    @admin.action(description='Change selected cases to under investigation')
    def change_to_searching(modeladmin, request, queryset):
     updated = queryset.update(status='under_investigation')
     messages.success(request, f"{updated} case status to under investigation.")
