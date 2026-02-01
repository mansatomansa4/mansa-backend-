from rest_framework import serializers
from .models import Event, EventImage, EventRegistration


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
    flyer = serializers.CharField(source='flyer_url', required=False, allow_blank=True, allow_null=True, read_only=True)
    time_display = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'category', 'date', 'start_time', 
            'end_time', 'location', 'is_virtual', 'virtual_link', 'status',
            'max_attendees', 'attendee_count', 'flyer', 'images', 'published',
            'created_by', 'time_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'flyer']
        
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
    flyer = serializers.CharField(source='flyer_url', required=False, allow_blank=True, allow_null=True, read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'category', 'date', 'start_time',
            'end_time', 'location', 'status', 'attendee_count', 'flyer',
            'images_count', 'published'
        ]

    def get_images_count(self, obj):
        return obj.images.count()


class EventRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for event registration"""
    event_id = serializers.UUIDField(write_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)
    event_date = serializers.DateField(source='event.date', read_only=True)

    class Meta:
        model = EventRegistration
        fields = [
            'id', 'event_id', 'event_title', 'event_date',
            'full_name', 'email', 'phone_number',
            'is_student', 'institution_name',
            'is_member', 'status',
            'registered_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'registered_at', 'created_at', 'updated_at']

    def validate(self, data):
        """Validate registration data"""
        # Check if event exists and is upcoming
        event_id = data.get('event_id')
        try:
            event = Event.objects.get(id=event_id)
            if event.status != 'upcoming':
                raise serializers.ValidationError({
                    'event_id': 'Cannot register for past events'
                })

            # Check if event has reached capacity
            if event.max_attendees and event.attendee_count >= event.max_attendees:
                raise serializers.ValidationError({
                    'event_id': 'Event has reached maximum capacity'
                })

            data['event'] = event
        except Event.DoesNotExist:
            raise serializers.ValidationError({
                'event_id': 'Event not found'
            })

        # Validate institution name for students
        if data.get('is_student') and not data.get('institution_name'):
            raise serializers.ValidationError({
                'institution_name': 'Institution name is required for students'
            })

        # Check for duplicate registration
        email = data.get('email')
        if EventRegistration.objects.filter(event=event, email=email).exists():
            raise serializers.ValidationError({
                'email': 'You have already registered for this event'
            })

        return data

    def create(self, validated_data):
        """Create registration and optionally link to member"""
        # Remove event_id from validated_data (we use 'event' instead)
        validated_data.pop('event_id', None)

        # Check if email belongs to an existing member
        email = validated_data.get('email')
        try:
            from apps.platform.models import Member
            member = Member.objects.get(email=email)
            validated_data['member_id'] = member.id
            validated_data['is_member'] = True
        except:
            # Not a member or Member model doesn't exist
            pass

        return super().create(validated_data)


class EventRegistrationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing registrations"""
    event_title = serializers.CharField(source='event.title', read_only=True)

    class Meta:
        model = EventRegistration
        fields = [
            'id', 'event_title', 'full_name', 'email',
            'is_student', 'is_member', 'status', 'registered_at'
        ]
