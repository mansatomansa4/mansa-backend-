from django.conf import settings
from django.db import models
from django.utils import timezone
import uuid

User = settings.AUTH_USER_MODEL


class Event(models.Model):
    """
    Model for community events that can be managed from the dashboard
    and displayed on the frontend events page.
    Uses existing Supabase events table.
    """
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('past', 'Past'),
    ]

    CATEGORY_CHOICES = [
        ('networking', 'Networking'),
        ('workshop', 'Workshop'),
        ('conference', 'Conference'),
        ('webinar', 'Webinar'),
        ('social', 'Social'),
        ('fundraiser', 'Fundraiser'),
        ('other', 'Other'),
    ]

    # Use UUID as primary key to match Supabase schema
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Information
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    
    # Event Details
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=255)
    is_virtual = models.BooleanField(default=False)
    virtual_link = models.TextField(blank=True, null=True)
    
    # Event Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    max_attendees = models.IntegerField(null=True, blank=True)
    attendee_count = models.IntegerField(default=0)
    
    # Media - store URL instead of ImageField for Supabase storage
    flyer_url = models.TextField(blank=True, null=True)
    
    # Metadata - use UUID for created_by to match Supabase auth.users
    created_by = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'events'
        managed = False  # Use existing Supabase table
        ordering = ['-date', '-start_time']
    
    def __str__(self):
        return f"{self.title} - {self.date}"
    
    def save(self, *args, **kwargs):
        # Auto-update status based on date
        if self.date < timezone.now().date():
            self.status = 'past'
        super().save(*args, **kwargs)


class EventImage(models.Model):
    """
    Model for multiple images per event (event photos/gallery)
    Uses existing Supabase event_images table.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='images', db_column='event_id')
    image_url = models.TextField(db_column='image_url')  # URL to Supabase storage
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    display_order = models.IntegerField(default=0, db_column='display_order')

    class Meta:
        db_table = 'event_images'
        managed = False  # Use existing Supabase table
        ordering = ['display_order', 'uploaded_at']

    def __str__(self):
        return f"Image for {self.event.title}"


class EventRegistration(models.Model):
    """
    Model for event registrations from users.
    Stores information about who registered for which event.
    Uses Supabase event_registrations table.
    """
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('attended', 'Attended'),
        ('no_show', 'No Show'),
    ]

    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Foreign key to events table
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='registrations',
        db_column='event_id'
    )

    # Registrant information
    full_name = models.TextField()
    email = models.TextField()
    phone_number = models.TextField()

    # Student information
    is_student = models.BooleanField(default=False)
    institution_name = models.TextField(blank=True, null=True)

    # Community membership
    is_member = models.BooleanField(default=False)

    # Optional: Link to members table if they are a member
    member_id = models.UUIDField(null=True, blank=True, db_column='member_id')

    # Registration status
    status = models.TextField(default='confirmed')

    # Cancellation tracking
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.UUIDField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True, null=True)

    # Email tracking
    confirmation_email_sent = models.BooleanField(default=False)
    confirmation_email_sent_at = models.DateTimeField(null=True, blank=True)
    reminder_email_sent = models.BooleanField(default=False)
    reminder_email_sent_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    registered_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Metadata for additional information (stored as JSONB in Supabase)
    # Note: Django doesn't have native JSONB field for non-Postgres DBs,
    # but since we're using Supabase (Postgres), we can use JSONField
    from django.db.models import JSONField
    metadata = JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'event_registrations'
        managed = False  # Use existing Supabase table
        ordering = ['-registered_at']
        constraints = [
            models.UniqueConstraint(
                fields=['event', 'email'],
                name='event_registrations_unique_email_per_event'
            )
        ]

    def __str__(self):
        return f"{self.full_name} - {self.event.title}"

    def save(self, *args, **kwargs):
        # Validate institution_name requirement for students
        if self.is_student and not self.institution_name:
            raise ValueError("Institution name is required for students")
        super().save(*args, **kwargs)
