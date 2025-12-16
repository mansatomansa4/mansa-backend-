from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import Event, EventImage
from .serializers import EventSerializer, EventListSerializer, EventImageSerializer


class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing events.
    
    Public users can view published events.
    Authenticated users (admins) can create, update, and delete events.
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'category', 'published']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['date', 'created_at', 'attendee_count']
    ordering = ['-date']
    
    def get_queryset(self):
        queryset = Event.objects.select_related('created_by').prefetch_related('images')
        
        # Public users only see published events
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(published=True)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return EventListSerializer
        return EventSerializer
    
    def create(self, request, *args, **kwargs):
        """Handle event creation with file uploads"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Save event with current user as creator
        event = serializer.save(created_by=request.user)
        
        # Handle multiple image uploads if provided
        images = request.FILES.getlist('images')
        if images:
            for image_file in images:
                EventImage.objects.create(
                    event=event,
                    image=image_file,
                    caption=request.data.get('caption', '')
                )
        
        # Re-serialize with images included
        output_serializer = self.get_serializer(event)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Handle event updates with file uploads"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Save updated event
        event = serializer.save()
        
        # Handle new image uploads if provided
        images = request.FILES.getlist('images')
        if images:
            for image_file in images:
                EventImage.objects.create(
                    event=event,
                    image=image_file,
                    caption=request.data.get('caption', '')
                )
        
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
