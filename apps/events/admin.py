from django.contrib import admin
from .models import Event


@admin.register(Event) 
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'team_a', 'team_b', 'start_time', 'status']
    list_filter = ['status', 'start_time']
    search_fields = ['name', 'team_a', 'team_b']
    ordering = ['-start_time']


