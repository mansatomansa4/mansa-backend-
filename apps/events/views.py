from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import Event, EventImage, EventRegistration
from .serializers import (
    EventSerializer, EventListSerializer, EventImageSerializer,
    EventRegistrationSerializer, EventRegistrationListSerializer
)


class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing events.
    
    Public users can view published events.
    Authenticated users (admins) can create, update, and delete events.
    """
    permission_classes = []  # Temporarily allow all for debugging
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'category', 'published']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['date', 'created_at', 'attendee_count']
    ordering = ['-date']
    
    def get_queryset(self):
        # Note: created_by is now a UUID field, not a ForeignKey, so no select_related needed
        queryset = Event.objects.prefetch_related('images')
        
        # Public users only see published events
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(published=True)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return EventListSerializer
        return EventSerializer
    
    def create(self, request, *args, **kwargs):
        """Handle event creation with file uploads to Supabase"""
        import logging
        from apps.core.supabase_storage import get_supabase_storage
        
        logger = logging.getLogger(__name__)
        logger.info(f"Received event creation request with data: {request.data}")
        logger.info(f"FILES: {request.FILES}")
        
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Validation errors: {serializer.errors}")
        serializer.is_valid(raise_exception=True)
        
        # Get user ID (UUID) - for now, set to None as we're using JWT tokens
        # In production, you'd map JWT user to Supabase auth.users UUID
        created_by_uuid = None
        if request.user.is_authenticated:
            # You can add logic here to get the Supabase UUID from your users table
            # For now, we'll leave it as None
            pass
        
        # Save event
        event = serializer.save(created_by=created_by_uuid)
        
        # Upload files to Supabase Storage
        try:
            storage = get_supabase_storage()
        except Exception as e:
            logger.error(f"Failed to initialize Supabase storage: {e}")
            # Return event without file uploads if storage is not configured
            output_serializer = self.get_serializer(event)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        
        # Handle flyer upload if provided
        flyer_file = request.FILES.get('flyer')
        if flyer_file:
            try:
                flyer_url = storage.upload_file(
                    file=flyer_file,
                    bucket_name='event-flyers',
                    folder=''
                )
                event.flyer_url = flyer_url
                event.save()
                logger.info(f"Uploaded flyer to: {flyer_url}")
            except Exception as e:
                logger.error(f"Error uploading flyer: {e}")
        
        # Handle multiple image uploads if provided
        images = request.FILES.getlist('images')
        if images:
            for idx, image_file in enumerate(images):
                try:
                    image_url = storage.upload_file(
                        file=image_file,
                        bucket_name='event-photos',
                        folder=''
                    )
                    EventImage.objects.create(
                        event=event,
                        image_url=image_url,
                        display_order=idx
                    )
                    logger.info(f"Uploaded image to: {image_url}")
                except Exception as e:
                    logger.error(f"Error uploading image: {e}")
        
        # Re-serialize with images included
        output_serializer = self.get_serializer(event)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Handle event updates with file uploads to Supabase"""
        import logging
        from apps.core.supabase_storage import get_supabase_storage
        
        logger = logging.getLogger(__name__)
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Save updated event
        event = serializer.save()
        
        # Upload files to Supabase Storage
        storage = get_supabase_storage()
        
        # Handle flyer upload if provided
        flyer_file = request.FILES.get('flyer')
        if flyer_file:
            try:
                # Delete old flyer if exists
                if event.flyer_url:
                    old_path = event.flyer_url.split('/event-flyers/')[-1]
                    storage.delete_file('event-flyers', old_path)
                
                # Upload new flyer
                flyer_url = storage.upload_file(
                    file=flyer_file,
                    bucket_name='event-flyers',
                    folder=''
                )
                event.flyer_url = flyer_url
                event.save()
                logger.info(f"Uploaded new flyer to: {flyer_url}")
            except Exception as e:
                logger.error(f"Error uploading flyer: {e}")
        
        # Handle new image uploads if provided
        images = request.FILES.getlist('images')
        if images:
            # Get current max display_order
            max_order = event.images.aggregate(models.Max('display_order'))['display_order__max'] or 0
            
            for idx, image_file in enumerate(images):
                try:
                    image_url = storage.upload_file(
                        file=image_file,
                        bucket_name='event-photos',
                        folder=''
                    )
                    EventImage.objects.create(
                        event=event,
                        image_url=image_url,
                        display_order=max_order + idx + 1
                    )
                    logger.info(f"Uploaded image to: {image_url}")
                except Exception as e:
                    logger.error(f"Error uploading image: {e}")
        
        # Re-serialize with images included
        output_serializer = self.get_serializer(event)
        return Response(output_serializer.data)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get all upcoming published events"""
        events = self.get_queryset().filter(
            status='upcoming',
            published=True,
            date__gte=timezone.now().date()
        )
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def past(self, request):
        """Get all past published events"""
        events = self.get_queryset().filter(
            status='past',
            published=True
        )
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def move_to_past(self, request, pk=None):
        """Move an event from upcoming to past"""
        event = self.get_object()
        event.status = 'past'
        event.save()
        serializer = self.get_serializer(event)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def move_to_upcoming(self, request, pk=None):
        """Move an event from past to upcoming"""
        event = self.get_object()
        event.status = 'upcoming'
        event.save()
        serializer = self.get_serializer(event)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_publish(self, request, pk=None):
        """Toggle publish status of an event"""
        event = self.get_object()
        event.published = not event.published
        event.save()
        serializer = self.get_serializer(event)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def upload_images(self, request, pk=None):
        """Upload multiple images to an event"""
        event = self.get_object()
        images = request.FILES.getlist('images')
        
        if not images:
            return Response(
                {'error': 'No images provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_images = []
        for image in images:
            event_image = EventImage.objects.create(
                event=event,
                image=image,
                caption=request.data.get('caption', '')
            )
            created_images.append(event_image)
        
        serializer = EventImageSerializer(created_images, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def delete_image(self, request, pk=None):
        """Delete an event image"""
        image_id = request.data.get('image_id')
        if not image_id:
            return Response(
                {'error': 'image_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            event = self.get_object()
            image = EventImage.objects.get(id=image_id, event=event)
            image.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except EventImage.DoesNotExist:
            return Response(
                {'error': 'Image not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'], permission_classes=[])
    def registrations(self, request, pk=None):
        """Get all registrations for a specific event (admin only in production)"""
        event = self.get_object()
        registrations = EventRegistration.objects.filter(event=event)

        # In production, you might want to add permission checks here
        # if not request.user.is_staff:
        #     return Response({'error': 'Permission denied'}, status=403)

        serializer = EventRegistrationListSerializer(registrations, many=True)
        return Response(serializer.data)


class EventRegistrationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing event registrations.

    Public users can create registrations.
    Admins can view all registrations.
    """
    permission_classes = []  # Allow public registration
    serializer_class = EventRegistrationSerializer
    queryset = EventRegistration.objects.select_related('event').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event', 'status', 'is_student', 'is_member']
    search_fields = ['full_name', 'email', 'phone_number']
    ordering_fields = ['registered_at', 'full_name']
    ordering = ['-registered_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return EventRegistrationListSerializer
        return EventRegistrationSerializer

    def create(self, request, *args, **kwargs):
        """Handle event registration without email notification"""
        import logging
        logger = logging.getLogger(__name__)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create registration
        registration = serializer.save()

        # # Send confirmation email
        # try:
        #     self._send_confirmation_email(registration)
        #     registration.confirmation_email_sent = True
        #     registration.confirmation_email_sent_at = timezone.now()
        #     registration.save()
        # except Exception as e:
        #     logger.error(f"Failed to send confirmation email: {e}")
        #     # Don't fail the registration if email fails

        output_serializer = self.get_serializer(registration)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def _send_confirmation_email(self, registration):
        """Send confirmation email to registrant"""
        from django.core.mail import send_mail
        from django.conf import settings

        subject = f"Registration Confirmed: {registration.event.title}"

        # Format date and time
        event_date = registration.event.date.strftime('%A, %B %d, %Y')
        event_time = f"{registration.event.start_time.strftime('%I:%M %p')} - {registration.event.end_time.strftime('%I:%M %p')}"

        # Build message
        message = f"""Hi {registration.full_name},

Thank you for registering for {registration.event.title}!

Event Details:
- Date: {event_date}
- Time: {event_time}
- Location: {registration.event.location}

We're excited to see you there!
"""

        # Add join community message for non-members
        if not registration.is_member:
            frontend_url = settings.FRONTEND_URL or 'https://your-domain.com'
            message += f"""
We noticed you're not a member of the Mansa-to-Mansa community yet.
Join us at: {frontend_url}/signup
"""

        message += """
Best regards,
The Mansa-to-Mansa Team
"""

        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[registration.email],
            fail_silently=False,
        )

    @action(detail=False, methods=['get'], permission_classes=[])
    def check_registration(self, request):
        """Check if user is already registered for an event"""
        event_id = request.query_params.get('event_id')
        email = request.query_params.get('email')

        if not event_id or not email:
            return Response(
                {'error': 'event_id and email are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            registration = EventRegistration.objects.get(
                event_id=event_id,
                email=email
            )
            return Response({
                'registered': True,
                'registration': {
                    'id': registration.id,
                    'registered_at': registration.registered_at,
                    'status': registration.status
                }
            })
        except EventRegistration.DoesNotExist:
            return Response({'registered': False})

    @action(detail=True, methods=['post'], permission_classes=[])
    def cancel(self, request, pk=None):
        """Cancel a registration"""
        registration = self.get_object()

        # Check if event hasn't passed
        if registration.event.status == 'past':
            return Response(
                {'error': 'Cannot cancel registration for past events'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update status
        registration.status = 'cancelled'
        registration.cancelled_at = timezone.now()
        registration.cancellation_reason = request.data.get('reason', '')
        registration.save()

        serializer = self.get_serializer(registration)
        return Response(serializer.data)
