"""
Mentorship App Models

These are proxy models for Django admin integration.
Actual data is stored in Supabase and accessed via supabase_client.py
"""
from django.db import models


class MentorProxy(models.Model):
    """
    Proxy model for mentor data stored in Supabase.
    This allows Django admin integration without actual database tables.
    """
    class Meta:
        managed = False
        db_table = 'mentors'
        verbose_name = 'Mentor'
        verbose_name_plural = 'Mentors'


class BookingProxy(models.Model):
    """
    Proxy model for booking data stored in Supabase.
    """
    class Meta:
        managed = False
        db_table = 'mentorship_bookings'
        verbose_name = 'Mentorship Booking'
        verbose_name_plural = 'Mentorship Bookings'
