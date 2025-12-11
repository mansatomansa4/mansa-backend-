from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class Event(models.Model):
    """
    Model for community events that can be managed from the dashboard
    and displayed on the frontend events page.
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
    virtual_link = models.URLField(blank=True, null=True)
    
    # Event Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    max_attendees = models.IntegerField(null=True, blank=True)
    attendee_count = models.IntegerField(default=0)
    
    # Media
    flyer = models.ImageField(upload_to='events/flyers/', blank=True, null=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-date', '-start_time']
        indexes = [
            models.Index(fields=['status', 'date']),
            models.Index(fields=['published', 'status']),
        ]
    
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
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='events/photos/')
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'uploaded_at']
    
    def __str__(self):
        return f"Image for {self.event.title}"
