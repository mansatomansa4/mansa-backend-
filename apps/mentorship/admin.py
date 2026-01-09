"""
Django Admin Configuration for Mentorship App

Provides admin interface for managing mentors and bookings.
Note: These are proxy models for Supabase data, so admin is simplified.
"""
from django.contrib import admin
from .models import MentorProxy, BookingProxy


@admin.register(MentorProxy)
class MentorAdmin(admin.ModelAdmin):
    list_display = ('id',)
    search_fields = ()
    

@admin.register(BookingProxy)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id',)
    search_fields = ()
