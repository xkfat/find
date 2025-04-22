from django.contrib import admin
from .models import MissingPerson


@admin.register(MissingPerson)
class MissingPersonAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'status', 'reporter', 'date_reported')
    search_fields = ('first_name', 'last_name', 'status', 'reporter__username')
    list_filter = ('status', 'gender')