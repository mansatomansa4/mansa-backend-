from django.contrib import admin
from .models import Event, EventImage, EventRegistration


class EventImageInline(admin.TabularInline):
    model = EventImage
    extra = 1
    fields = ['image_url', 'caption', 'display_order']


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
            'fields': ('flyer_url',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EventImage)
class EventImageAdmin(admin.ModelAdmin):
    list_display = ['event', 'caption', 'display_order', 'uploaded_at']
    list_filter = ['event', 'uploaded_at']
    search_fields = ['event__title', 'caption']


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'email', 'event', 'is_student',
        'is_member', 'status', 'registered_at'
    ]
    list_filter = ['status', 'is_student', 'is_member', 'event', 'registered_at']
    search_fields = ['full_name', 'email', 'phone_number', 'event__title']
    readonly_fields = [
        'id', 'registered_at', 'created_at', 'updated_at',
        'confirmation_email_sent_at', 'reminder_email_sent_at'
    ]
    date_hierarchy = 'registered_at'

    fieldsets = (
        ('Event Information', {
            'fields': ('event', 'status')
        }),
        ('Registrant Details', {
            'fields': ('full_name', 'email', 'phone_number')
        }),
        ('Student Information', {
            'fields': ('is_student', 'institution_name')
        }),
        ('Community Membership', {
            'fields': ('is_member', 'member_id')
        }),
        ('Email Tracking', {
            'fields': (
                'confirmation_email_sent', 'confirmation_email_sent_at',
                'reminder_email_sent', 'reminder_email_sent_at'
            ),
            'classes': ('collapse',)
        }),
        ('Cancellation', {
            'fields': ('cancelled_at', 'cancelled_by', 'cancellation_reason'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'registered_at', 'created_at', 'updated_at', 'metadata'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_attended', 'mark_as_no_show', 'export_as_csv']

    def mark_as_attended(self, request, queryset):
        updated = queryset.update(status='attended')
        self.message_user(request, f'{updated} registrations marked as attended.')
    mark_as_attended.short_description = "Mark selected as attended"

    def mark_as_no_show(self, request, queryset):
        updated = queryset.update(status='no_show')
        self.message_user(request, f'{updated} registrations marked as no show.')
    mark_as_no_show.short_description = "Mark selected as no show"

    def export_as_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="event_registrations.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Event', 'Full Name', 'Email', 'Phone', 'Is Student',
            'Institution', 'Is Member', 'Status', 'Registered At'
        ])

        for registration in queryset:
            writer.writerow([
                registration.event.title,
                registration.full_name,
                registration.email,
                registration.phone_number,
                'Yes' if registration.is_student else 'No',
                registration.institution_name or 'N/A',
                'Yes' if registration.is_member else 'No',
                registration.status,
                registration.registered_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

        return response
    export_as_csv.short_description = "Export selected as CSV"
