"""
Mentorship App Models

These are proxy models for Django admin integration.
Actual data is stored in Supabase and accessed via supabase_client.py
"""
from django.db import models


class Mentor(models.Model):
    """
    Mentor model linked to Members table.
    Auto-created when member has membershiptype='mentor'
    """
    id = models.UUIDField(primary_key=True)
    member_id = models.UUIDField(null=True, blank=True)  # Links to members table
    user_id = models.IntegerField(default=0)
    bio = models.TextField(null=True, blank=True)
    photo_url = models.TextField(null=True, blank=True)
    expertise = models.JSONField(default=list)
    availability_timezone = models.CharField(max_length=50, default='UTC')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_sessions = models.IntegerField(default=0)
    is_approved = models.BooleanField(default=False)
    version = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = False
        db_table = 'mentors'
        verbose_name = 'Mentor'
        verbose_name_plural = 'Mentors'
    
    def __str__(self):
        return f"Mentor {self.id}"


class MentorAvailability(models.Model):
    """
    Mentor availability slots
    """
    id = models.UUIDField(primary_key=True)
    mentor_id = models.UUIDField()
    day_of_week = models.IntegerField(null=True, blank=True)  # 0-6 (Monday-Sunday)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_recurring = models.BooleanField(default=True)
    specific_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = False
        db_table = 'mentor_availability'
        verbose_name = 'Mentor Availability'
        verbose_name_plural = 'Mentor Availabilities'


class MentorshipBooking(models.Model):
    """
    Mentorship session bookings
    """
    id = models.UUIDField(primary_key=True)
    mentor_id = models.UUIDField()
    mentee_id = models.UUIDField()  # Links to members table
    session_date = models.DateTimeField()
    duration_minutes = models.IntegerField(default=60)
    session_type = models.TextField(default='one-on-one')
    status = models.TextField(default='pending')
    booking_status = models.TextField(default='pending')
    topic = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    mentee_goals = models.TextField(null=True, blank=True)
    mentor_feedback = models.TextField(null=True, blank=True)
    rating = models.IntegerField(null=True, blank=True)
    meeting_url = models.TextField(null=True, blank=True)
    meeting_platform = models.TextField(null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    reminder_sent = models.BooleanField(default=False)
    confirmation_sent = models.BooleanField(default=False)
    feedback_requested = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)
    cancellation_reason = models.TextField(null=True, blank=True)
    cancelled_by = models.UUIDField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.UUIDField(null=True, blank=True)
    updated_by = models.UUIDField(null=True, blank=True)
    
    class Meta:
        managed = False
        db_table = 'mentorship_bookings'
        verbose_name = 'Mentorship Booking'
        verbose_name_plural = 'Mentorship Bookings'
    
    def __str__(self):
        return f"Booking {self.id}"


# Legacy proxy models for backwards compatibility
class MentorProxy(Mentor):
    class Meta:
        proxy = True
        verbose_name = 'Mentor (Proxy)'
        verbose_name_plural = 'Mentors (Proxy)'


class BookingProxy(MentorshipBooking):
    class Meta:
        proxy = True
        verbose_name = 'Booking (Proxy)'
        verbose_name_plural = 'Bookings (Proxy)'
