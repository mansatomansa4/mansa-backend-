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
