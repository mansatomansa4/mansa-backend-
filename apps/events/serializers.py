from rest_framework import serializers
from .models import Event, EventImage


class EventImageSerializer(serializers.ModelSerializer):
    """Serializer for event images"""
    image = serializers.CharField(source='image_url')
    order = serializers.IntegerField(source='display_order', required=False, default=0)
    
    class Meta:
        model = EventImage
        fields = ['id', 'image', 'caption', 'uploaded_at', 'order']
        read_only_fields = ['id', 'uploaded_at']


class EventSerializer(serializers.ModelSerializer):
    """Serializer for Event model"""
    images = EventImageSerializer(many=True, read_only=True)
    flyer = serializers.CharField(source='flyer_url', required=False, allow_blank=True, allow_null=True)
    time_display = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'category', 'date', 'start_time', 
            'end_time', 'location', 'is_virtual', 'virtual_link', 'status',
            'max_attendees', 'attendee_count', 'flyer', 'images', 'published',
            'created_by', 'time_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
        
    def validate_virtual_link(self, value):
        """Ensure virtual_link is provided if is_virtual is True"""
        if self.initial_data.get('is_virtual') and not value:
            return None  # Allow empty for now
        return value
    
    def get_time_display(self, obj):
        return f"{obj.start_time.strftime('%I:%M %p')} - {obj.end_time.strftime('%I:%M %p')}"


class EventListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for event lists"""
    images_count = serializers.SerializerMethodField()
    flyer = serializers.CharField(source='flyer_url', required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'category', 'date', 'start_time', 
            'end_time', 'location', 'status', 'attendee_count', 'flyer', 
            'images_count', 'published'
        ]
    
    def get_images_count(self, obj):
        return obj.images.count()
