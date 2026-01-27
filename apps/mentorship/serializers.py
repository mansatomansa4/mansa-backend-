"""
Mentorship Serializers for Django REST Framework

Comprehensive serializers with validation for mentor profiles, availability, and bookings.
"""
from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, timedelta
from typing import Dict, List
import uuid


class ExpertiseSerializer(serializers.Serializer):
    """Nested serializer for expertise categories"""
    category = serializers.CharField(max_length=100)
    subcategories = serializers.ListField(
        child=serializers.CharField(max_length=200),
        required=False,
        allow_empty=True
    )


class MentorProfileSerializer(serializers.Serializer):
    """Mentor Profile Serializer"""
    id = serializers.UUIDField(read_only=True)
    user_id = serializers.IntegerField()
    bio = serializers.CharField(max_length=2000, allow_blank=True)
    photo_url = serializers.URLField(required=False, allow_null=True)
    expertise = serializers.JSONField()  # Array of expertise objects
    rating = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)
    total_sessions = serializers.IntegerField(read_only=True)
    is_approved = serializers.BooleanField(read_only=True)
    linkedin_url = serializers.URLField(required=False, allow_null=True, allow_blank=True)
    github_url = serializers.URLField(required=False, allow_null=True, allow_blank=True)
    twitter_url = serializers.URLField(required=False, allow_null=True, allow_blank=True)
    years_of_experience = serializers.IntegerField(required=False, allow_null=True)
    company = serializers.CharField(max_length=200, required=False, allow_blank=True)
    job_title = serializers.CharField(max_length=200, required=False, allow_blank=True)
    timezone = serializers.CharField(max_length=50, default='UTC')
    version = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    def validate_expertise(self, value):
        """Validate expertise is array of objects with category field"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Expertise must be an array")
        
        if len(value) == 0:
            raise serializers.ValidationError("At least one expertise area is required")
        
        if len(value) > 10:
            raise serializers.ValidationError("Maximum 10 expertise areas allowed")
        
        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError("Each expertise must be an object")
            if 'category' not in item:
                raise serializers.ValidationError("Each expertise must have a 'category' field")
        
        return value
    
    def validate_years_of_experience(self, value):
        """Validate years of experience"""
        if value is not None and (value < 0 or value > 50):
            raise serializers.ValidationError("Years of experience must be between 0 and 50")
        return value
    
    def validate_bio(self, value):
        """Validate bio length"""
        if len(value) < 50:
            raise serializers.ValidationError("Bio must be at least 50 characters")
        return value


class AvailabilitySlotSerializer(serializers.Serializer):
    """Availability Slot Serializer"""
    id = serializers.UUIDField(read_only=True)
    mentor_id = serializers.UUIDField()
    day_of_week = serializers.IntegerField(min_value=0, max_value=6, required=False, allow_null=True)
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    specific_date = serializers.DateField(required=False, allow_null=True)
    is_recurring = serializers.BooleanField(default=True)
    is_active = serializers.BooleanField(default=True)
    created_at = serializers.DateTimeField(read_only=True)
    
    def validate(self, data):
        """Cross-field validation"""
        # Either recurring OR specific date, not both
        if data.get('is_recurring') and data.get('specific_date'):
            raise serializers.ValidationError(
                "Slot cannot be both recurring and have a specific date"
            )
        
        # If recurring, day_of_week is required
        if data.get('is_recurring', True) and 'day_of_week' not in data:
            raise serializers.ValidationError(
                "day_of_week is required for recurring slots"
            )
        
        # If specific date, it must be in the future
        if data.get('specific_date') and data['specific_date'] < timezone.now().date():
            raise serializers.ValidationError(
                "specific_date must be in the future"
            )
        
        # End time must be after start time
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError(
                "end_time must be after start_time"
            )
        
        # Slot duration must be at least 30 minutes
        start = datetime.combine(timezone.now().date(), data['start_time'])
        end = datetime.combine(timezone.now().date(), data['end_time'])
        duration = (end - start).seconds / 60
        
        if duration < 30:
            raise serializers.ValidationError(
                "Slot duration must be at least 30 minutes"
            )
        
        if duration > 180:
            raise serializers.ValidationError(
                "Slot duration cannot exceed 3 hours"
            )
        
        return data


class BookingSerializer(serializers.Serializer):
    """Mentorship Booking Serializer"""
    id = serializers.UUIDField(read_only=True)
    mentor_id = serializers.UUIDField()
    mentee_id = serializers.IntegerField(required=False)
    session_date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    duration_minutes = serializers.IntegerField(required=False, min_value=30, max_value=120)
    session_type = serializers.CharField(max_length=50, required=False, default='one-on-one')
    topic = serializers.CharField(max_length=500)
    description = serializers.CharField(max_length=2000, allow_blank=True)
    mentee_goals = serializers.CharField(max_length=2000, required=False, allow_blank=True, allow_null=True)
    status = serializers.ChoiceField(
        choices=['pending', 'confirmed', 'completed', 'cancelled_by_mentee', 'cancelled_by_mentor'],
        default='pending'
    )
    meeting_url = serializers.URLField(required=False, allow_null=True, allow_blank=True)
    notes = serializers.CharField(max_length=2000, required=False, allow_blank=True, allow_null=True)
    mentor_feedback = serializers.CharField(max_length=2000, required=False, allow_blank=True, allow_null=True)
    rating = serializers.IntegerField(min_value=1, max_value=5, required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    def validate_session_date(self, value):
        """Validate session date is in the future"""
        if value < timezone.now().date():
            raise serializers.ValidationError("Session date must be in the future")
        
        # Cannot book more than 3 months in advance
        three_months = timezone.now().date() + timedelta(days=90)
        if value > three_months:
            raise serializers.ValidationError("Cannot book more than 3 months in advance")
        
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        # End time must be after start time
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError(
                "end_time must be after start_time"
            )
        
        # Session duration validation
        start = datetime.combine(data['session_date'], data['start_time'])
        end = datetime.combine(data['session_date'], data['end_time'])
        duration = (end - start).seconds / 60
        
        if duration < 30:
            raise serializers.ValidationError(
                "Session duration must be at least 30 minutes"
            )
        
        if duration > 120:
            raise serializers.ValidationError(
                "Session duration cannot exceed 2 hours"
            )
        
        return data


class BookingStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating booking status"""
    status = serializers.ChoiceField(
        choices=['confirmed', 'completed', 'cancelled_by_mentee', 'cancelled_by_mentor']
    )
    mentor_notes = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    meeting_link = serializers.URLField(required=False, allow_blank=True)
    version = serializers.IntegerField(required=True)  # For optimistic locking


class BookingFeedbackSerializer(serializers.Serializer):
    """Serializer for adding feedback to completed bookings"""
    rating = serializers.IntegerField(min_value=1, max_value=5)
    feedback = serializers.CharField(max_length=1000, allow_blank=True)
    version = serializers.IntegerField(required=True)
    
    def validate_rating(self, value):
        """Validate rating"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value


class MentorStatsSerializer(serializers.Serializer):
    """Serializer for mentor statistics"""
    total_sessions = serializers.IntegerField()
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    pending_bookings = serializers.IntegerField()
    upcoming_sessions = serializers.IntegerField()
    completed_sessions = serializers.IntegerField()


class ExpertiseCategorySerializer(serializers.Serializer):
    """Expertise category from mentorship_expertise table"""
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(max_length=500, allow_blank=True)
    icon = serializers.CharField(max_length=50, required=False)
    color = serializers.CharField(max_length=20, required=False)
    is_active = serializers.BooleanField(default=True)
