from django.contrib import admin
from .models import Event, EventImage


class EventImageInline(admin.TabularInline):
    model = EventImage
    extra = 1
    fields = ['image', 'caption', 'order']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'status', 'category', 'location', 'attendee_count', 'published', 'created_at']
    list_filter = ['status', 'category', 'published', 'is_virtual', 'date']
    search_fields = ['title', 'description', 'location']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    inlines = [EventImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category')
        }),
        ('Event Details', {
            'fields': ('date', 'start_time', 'end_time', 'location', 'is_virtual', 'virtual_link')
        }),
        ('Capacity & Status', {
            'fields': ('status', 'max_attendees', 'attendee_count', 'published')
        }),
        ('Media', {
            'fields': ('flyer',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(EventImage)
class EventImageAdmin(admin.ModelAdmin):
    list_display = ['event', 'caption', 'order', 'uploaded_at']
    list_filter = ['event', 'uploaded_at']
    search_fields = ['event__title', 'caption']
