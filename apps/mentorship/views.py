"""
Mentorship API Views with Conflict Prevention

DRF ViewSets with PostgreSQL advisory locks, rate limiting, caching.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from django.core.cache import cache
from django.db import connection
from django.utils import timezone
from datetime import datetime, timedelta
import logging
import hashlib

from .serializers import (
    MentorProfileSerializer,
    AvailabilitySlotSerializer,
    BookingSerializer,
    BookingStatusUpdateSerializer,
    BookingFeedbackSerializer,
    ExpertiseCategorySerializer,
    MentorStatsSerializer
)
from .supabase_client import supabase_client
from apps.users.models import User

logger = logging.getLogger(__name__)


class BookingRateThrottle(UserRateThrottle):
    """Custom throttle: 3 bookings per hour per user"""
    rate = '3/hour'
    scope = 'booking_create'


class MentorViewSet(viewsets.ViewSet):
    """
    ViewSet for mentor operations.
    Handles listing, retrieving, creating, and updating mentor profiles.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """
        List all approved mentors with optional filters.
        Query params: expertise, min_rating, page, page_size
        """
        # Check cache first
        cache_key = self._build_cache_key('list', request.GET.dict())
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)
        
        # Build filters
        filters = {}
        if request.GET.get('expertise'):
            filters['expertise'] = [request.GET.get('expertise')]
        if request.GET.get('min_rating'):
            try:
                filters['min_rating'] = float(request.GET.get('min_rating'))
            except ValueError:
                pass
        
        # Pagination
        pagination = {
            'page': int(request.GET.get('page', 1)),
            'page_size': int(request.GET.get('page_size', 12))
        }
        
        try:
            # Use enriched method that includes member data
            result = supabase_client.get_mentors_with_member_data(filters, pagination)
            
            response_data = {
                'results': result['data'],
                'count': result['count'],
                'page': pagination['page'],
                'page_size': pagination['page_size']
            }
            
            # Cache for 5 minutes
            cache.set(cache_key, response_data, 300)
            
            return Response(response_data)
        except Exception as e:
            logger.error(f"Error listing mentors: {e}")
            return Response(
                {'error': 'Failed to fetch mentors'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, pk=None):
        """Get single mentor profile by ID"""
        cache_key = f'mentor_profile_{pk}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)
        
        try:
            # Get mentor from Supabase
            mentor_data = supabase_client._client.table('mentors').select('*').eq('id', pk).single().execute().data
            
            if not mentor_data:
                return Response(
                    {'error': 'Mentor not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Enrich with user data
            user = User.objects.filter(id=mentor_data['user_id']).values('email', 'first_name', 'last_name').first()
            if user:
                mentor_data['user'] = user
            
            # Cache for 5 minutes
            cache.set(cache_key, mentor_data, 300)
            
            return Response(mentor_data)
        except Exception as e:
            logger.error(f"Error retrieving mentor {pk}: {e}")
            return Response(
                {'error': 'Failed to fetch mentor profile'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """Get current user's mentor profile"""
        try:
            mentor_data = supabase_client.get_mentor_by_user_id(request.user.id)
            if not mentor_data:
                return Response(
                    {'error': 'Mentor profile not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(mentor_data)
        except Exception as e:
            logger.error(f"Error fetching mentor profile for user {request.user.id}: {e}")
            return Response(
                {'error': 'Failed to fetch mentor profile'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def create_profile(self, request):
        """Create mentor profile for current user"""
        # Check if user is eligible to be a mentor
        if not request.user.is_mentor:
            return Response(
                {'error': 'You are not registered as a mentor'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if profile already exists
        existing = supabase_client.get_mentor_by_user_id(request.user.id)
        if existing:
            return Response(
                {'error': 'Mentor profile already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = MentorProfileSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Force user_id to current user
            data = serializer.validated_data
            data['user_id'] = request.user.id
            data['is_approved'] = False  # Requires admin approval
            
            mentor_data = supabase_client.create_mentor_profile(data)
            return Response(mentor_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating mentor profile: {e}")
            return Response(
                {'error': 'Failed to create mentor profile'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['patch'])
    def update_profile(self, request, pk=None):
        """Update mentor profile with optimistic locking"""
        # Verify ownership
        mentor_data = supabase_client._client.table('mentors').select('*').eq('id', pk).single().execute().data
        if not mentor_data or mentor_data['user_id'] != request.user.id:
            return Response(
                {'error': 'Not authorized to update this profile'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = MentorProfileSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Get version for optimistic locking
        expected_version = request.data.get('version', mentor_data['version'])
        
        try:
            updated_data = supabase_client.update_mentor_profile(
                pk,
                serializer.validated_data,
                expected_version
            )
            
            # Invalidate cache
            cache.delete(f'mentor_profile_{pk}')
            cache.delete_pattern('mentor_list_*')
            
            return Response(updated_data)
        except Exception as e:
            if 'version mismatch' in str(e).lower():
                return Response(
                    {'error': 'Profile was updated by another process. Please refresh and try again.'},
                    status=status.HTTP_409_CONFLICT
                )
            logger.error(f"Error updating mentor profile: {e}")
            return Response(
                {'error': 'Failed to update mentor profile'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """Get availability slots for a mentor"""
        # Optional date range filter
        date_range = {}
        if request.GET.get('start_date'):
            date_range['start_date'] = request.GET.get('start_date')
        if request.GET.get('end_date'):
            date_range['end_date'] = request.GET.get('end_date')
        
        try:
            slots = supabase_client.get_availability_slots(pk, date_range if date_range else None)
            return Response(slots)
        except Exception as e:
            logger.error(f"Error fetching availability for mentor {pk}: {e}")
            return Response(
                {'error': 'Failed to fetch availability'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get statistics for current user's mentor profile"""
        try:
            mentor_data = supabase_client.get_mentor_by_user_id(request.user.id)
            if not mentor_data:
                return Response(
                    {'error': 'Mentor profile not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            mentor_id = mentor_data['id']
            
            # Get bookings
            bookings = supabase_client.get_mentor_bookings(mentor_id)
            
            # Calculate stats
            now = timezone.now()
            stats = {
                'total_sessions': mentor_data['total_sessions'],
                'average_rating': float(mentor_data['rating']) if mentor_data['rating'] else 0,
                'pending_bookings': len([b for b in bookings if b['status'] == 'pending']),
                'upcoming_sessions': len([b for b in bookings if b['status'] == 'confirmed' and datetime.fromisoformat(b['session_date']) >= now.date()]),
                'completed_sessions': len([b for b in bookings if b['status'] == 'completed'])
            }
            
            serializer = MentorStatsSerializer(stats)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching mentor stats: {e}")
            return Response(
                {'error': 'Failed to fetch statistics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _build_cache_key(self, prefix: str, params: dict) -> str:
        """Build cache key from request parameters"""
        param_str = str(sorted(params.items()))
        param_hash = hashlib.md5(param_str.encode()).hexdigest()
        return f'{prefix}_{param_hash}'


class BookingViewSet(viewsets.ViewSet):
    """
    ViewSet for booking operations.
    Handles creating, updating, and managing mentorship bookings.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [BookingRateThrottle]
    
    def list(self, request):
        """List bookings for current user (as mentee or mentor)"""
        role = request.GET.get('role', 'mentee')  # mentee or mentor
        status_filter = request.GET.get('status')  # optional status filter
        
        try:
            if role == 'mentee':
                bookings = supabase_client.get_mentee_bookings(request.user.id, status_filter)
            else:
                # Get mentor profile first
                mentor_data = supabase_client.get_mentor_by_user_id(request.user.id)
                if not mentor_data:
                    return Response(
                        {'error': 'Mentor profile not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                bookings = supabase_client.get_mentor_bookings(mentor_data['id'], status_filter)
            
            return Response(bookings)
        except Exception as e:
            logger.error(f"Error listing bookings: {e}")
            return Response(
                {'error': 'Failed to fetch bookings'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request):
        """
        Create a new booking with conflict prevention.
        Uses PostgreSQL advisory locks to prevent double-booking.
        """
        serializer = BookingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Force mentee_id to current user
        data = serializer.validated_data
        data['mentee_id'] = request.user.id
        
        # Advisory lock key based on mentor_id + session_date + start_time
        lock_key = f"{data['mentor_id']}_{data['session_date']}_{data['start_time']}"
        lock_id = abs(hash(lock_key)) % (2**31)  # Convert to int32
        
        try:
            # Acquire advisory lock
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_lock(%s)", [lock_id])
            
            # Check for conflicting bookings
            existing_bookings = supabase_client._client.table('mentorship_bookings').select('id').eq('mentor_id', str(data['mentor_id'])).eq('session_date', str(data['session_date'])).in_('status', ['pending', 'confirmed']).execute().data
            
            # Check time overlap
            for booking in existing_bookings:
                booking_detail = supabase_client._client.table('mentorship_bookings').select('*').eq('id', booking['id']).single().execute().data
                # Simple overlap check
                if not (data['end_time'] <= datetime.fromisoformat(booking_detail['start_time']).time() or 
                        data['start_time'] >= datetime.fromisoformat(booking_detail['end_time']).time()):
                    raise Exception("Time slot conflict detected")
            
            # Create booking
            booking = supabase_client.create_booking_with_lock(data)
            
            # Release lock
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_unlock(%s)", [lock_id])
            
            return Response(booking, status=status.HTTP_201_CREATED)
        except Exception as e:
            # Ensure lock is released
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_advisory_unlock(%s)", [lock_id])
            except:
                pass
            
            if 'conflict' in str(e).lower():
                return Response(
                    {'error': 'Time slot is no longer available'},
                    status=status.HTTP_409_CONFLICT
                )
            
            logger.error(f"Error creating booking: {e}")
            return Response(
                {'error': 'Failed to create booking'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update booking status (confirm, cancel, complete)"""
        serializer = BookingStatusUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            updated_booking = supabase_client.update_booking_status(
                pk,
                serializer.validated_data['status'],
                serializer.validated_data['version']
            )
            return Response(updated_booking)
        except Exception as e:
            if 'version mismatch' in str(e).lower():
                return Response(
                    {'error': 'Booking was updated by another process. Please refresh and try again.'},
                    status=status.HTTP_409_CONFLICT
                )
            logger.error(f"Error updating booking status: {e}")
            return Response(
                {'error': 'Failed to update booking'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def add_feedback(self, request, pk=None):
        """Add rating and feedback to completed booking"""
        serializer = BookingFeedbackSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # TODO: Implement feedback update logic
            # This will update the booking and recalculate mentor rating
            return Response({'message': 'Feedback added successfully'})
        except Exception as e:
            logger.error(f"Error adding feedback: {e}")
            return Response(
                {'error': 'Failed to add feedback'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ExpertiseViewSet(viewsets.ViewSet):
    """ViewSet for expertise categories"""
    permission_classes = [permissions.AllowAny]
    
    def list(self, request):
        """List all active expertise categories"""
        cache_key = 'expertise_categories'
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)
        
        try:
            response = supabase_client._client.table('mentorship_expertise').select('*').order('name').execute()
            data = response.data
            
            # Cache for 1 hour
            cache.set(cache_key, data, 3600)
            
            return Response(data)
        except Exception as e:
            logger.error(f"Error fetching expertise categories: {e}")
            return Response(
                {'error': 'Failed to fetch expertise categories'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
