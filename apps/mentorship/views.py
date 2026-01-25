"""
Mentorship API Views - Comprehensive Endpoints for Mentors and Mentees

DRF ViewSets with PostgreSQL advisory locks, rate limiting, caching.
Includes: Profile management, availability, bookings, reviews, dashboard data.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.cache import cache
from django.db import connection
from django.utils import timezone
from django.core.files.storage import default_storage
from datetime import datetime, timedelta
import logging
import hashlib
import uuid

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
from .tasks import (
    send_mentor_booking_notification,
    send_booking_status_update_email,
)
from apps.users.models import User

logger = logging.getLogger(__name__)


class BookingRateThrottle(UserRateThrottle):
    """Custom throttle: 3 bookings per hour per user"""
    rate = '3/hour'
    scope = 'booking_create'


class MentorViewSet(viewsets.ViewSet):
    """
    ViewSet for mentor operations.

    Endpoints:
    - GET /mentors/ - List all approved mentors (with search/filter)
    - GET /mentors/{id}/ - Get mentor profile
    - GET /mentors/me/ - Get current user's mentor profile
    - GET /mentors/my_profile/ - Alias for /me/
    - POST /mentors/create_profile/ - Create mentor profile
    - PATCH /mentors/{id}/update_profile/ - Update mentor profile
    - POST /mentors/{id}/upload_photo/ - Upload profile photo
    - DELETE /mentors/{id}/delete_photo/ - Delete profile photo
    - GET /mentors/{id}/availability/ - Get mentor's availability
    - GET /mentors/stats/ - Get mentor statistics
    - GET /mentors/dashboard/ - Get complete mentor dashboard data
    - GET /mentors/search/ - Search mentors by name/expertise
    - GET /mentors/{id}/reviews/ - Get mentor reviews
    """
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_permissions(self):
        """Allow unauthenticated access to list, retrieve, availability, search, reviews"""
        if self.action in ['list', 'retrieve', 'availability', 'search', 'reviews']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def list(self, request):
        """
        List all approved mentors with optional filters.

        Query params:
        - expertise: Filter by expertise area
        - min_rating: Minimum rating (0-5)
        - search: Search by name or expertise
        - page: Page number (default: 1)
        - page_size: Results per page (default: 12)
        """
        cache_key = self._build_cache_key('mentor_list', request.GET.dict())
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
        if request.GET.get('search'):
            filters['search'] = request.GET.get('search')

        # Pagination
        pagination = {
            'page': int(request.GET.get('page', 1)),
            'page_size': int(request.GET.get('page_size', 12))
        }

        try:
            result = supabase_client.get_mentors_with_member_data(filters, pagination)

            response_data = {
                'results': result['data'],
                'count': result['count'],
                'page': pagination['page'],
                'page_size': pagination['page_size']
            }

            cache.set(cache_key, response_data, 300)
            return Response(response_data)
        except Exception as e:
            logger.error(f"Error listing mentors: {e}")
            return Response(
                {'error': 'Failed to fetch mentors'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, pk=None):
        """Get single mentor profile by ID. Use pk='me' for current user's profile."""
        if pk == 'me':
            if not request.user.is_authenticated:
                return Response(
                    {'error': 'Authentication required'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            return self.my_profile(request)

        cache_key = f'mentor_profile_{pk}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        try:
            filters = {'id': pk}
            pagination = {'page': 1, 'page_size': 1}
            result = supabase_client.get_mentors_with_member_data(filters, pagination)

            if not result['data']:
                return Response(
                    {'error': 'Mentor not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            mentor_data = result['data'][0]
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
        """Get current user's mentor profile with full details"""
        try:
            mentor_data = supabase_client.get_mentor_with_member_data(request.user.id)
            if not mentor_data:
                return Response(
                    {'error': 'Mentor profile not found. Please create one first.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            mentor_data['user'] = {
                'id': request.user.id,
                'name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.email,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name
            }

            return Response(mentor_data)
        except Exception as e:
            logger.error(f"Error fetching mentor profile for user {request.user.id}: {e}")
            return Response(
                {'error': 'Failed to fetch mentor profile'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """
        Get complete mentor dashboard data including:
        - Profile info
        - Statistics (total sessions, rating, etc.)
        - Upcoming sessions
        - Pending booking requests
        - Recent completed sessions
        - Recent reviews
        """
        try:
            mentor_data = supabase_client.get_mentor_by_user_id(request.user.id, request.user.email)
            if not mentor_data:
                return Response(
                    {'error': 'Mentor profile not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            mentor_id = mentor_data['id']
            now = timezone.now()
            today = now.date().isoformat()

            # Get all bookings
            all_bookings = supabase_client.get_mentor_bookings(mentor_id)

            # Categorize bookings
            pending_bookings = [b for b in all_bookings if b.get('status') == 'pending']
            confirmed_bookings = [b for b in all_bookings if b.get('status') == 'confirmed']
            completed_bookings = [b for b in all_bookings if b.get('status') == 'completed']

            # Upcoming sessions (confirmed and date >= today)
            upcoming_sessions = [
                b for b in confirmed_bookings
                if b.get('session_date', '') >= today
            ][:5]  # Limit to 5

            # Recent completed sessions
            recent_completed = sorted(
                completed_bookings,
                key=lambda x: x.get('session_date', ''),
                reverse=True
            )[:5]

            # Get reviews
            reviews = supabase_client.get_mentor_reviews(mentor_id, limit=5)

            # Get availability slots
            availability = supabase_client.get_availability_slots(mentor_id)

            # Calculate statistics
            stats = {
                'total_sessions': mentor_data.get('total_sessions', 0),
                'average_rating': float(mentor_data.get('rating', 0)) if mentor_data.get('rating') else 0,
                'total_reviews': len(supabase_client.get_mentor_reviews(mentor_id)),
                'pending_requests': len(pending_bookings),
                'upcoming_sessions': len([b for b in confirmed_bookings if b.get('session_date', '') >= today]),
                'completed_sessions': len(completed_bookings),
                'this_month_sessions': len([
                    b for b in completed_bookings
                    if b.get('session_date', '')[:7] == today[:7]
                ])
            }

            dashboard_data = {
                'profile': mentor_data,
                'stats': stats,
                'pending_bookings': pending_bookings[:10],
                'upcoming_sessions': upcoming_sessions,
                'recent_completed': recent_completed,
                'recent_reviews': reviews,
                'availability': {
                    'recurring_slots': [s for s in availability if s.get('is_recurring')],
                    'specific_date_slots': [s for s in availability if not s.get('is_recurring')]
                }
            }

            return Response(dashboard_data)
        except Exception as e:
            logger.error(f"Error fetching mentor dashboard: {e}")
            return Response(
                {'error': 'Failed to fetch dashboard data'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search mentors by name, expertise, or skills.

        Query params:
        - q: Search query
        - expertise: Filter by expertise
        - page, page_size: Pagination
        """
        query = request.GET.get('q', '').strip()
        expertise = request.GET.get('expertise', '').strip()

        if not query and not expertise:
            return Response(
                {'error': 'Please provide a search query (q) or expertise filter'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            filters = {}
            if query:
                filters['query'] = query
            if expertise:
                filters['expertise'] = [expertise]

            pagination = {
                'page': int(request.GET.get('page', 1)),
                'page_size': int(request.GET.get('page_size', 12))
            }

            result = supabase_client.search_mentors(filters, pagination)

            return Response({
                'results': result['data'],
                'count': result['count'],
                'query': query,
                'page': pagination['page'],
                'page_size': pagination['page_size']
            })
        except Exception as e:
            logger.error(f"Error searching mentors: {e}")
            return Response(
                {'error': 'Failed to search mentors'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def create_profile(self, request):
        """Create mentor profile for current user"""
        if not request.user.is_mentor:
            return Response(
                {'error': 'You are not registered as a mentor'},
                status=status.HTTP_403_FORBIDDEN
            )

        existing = supabase_client.get_mentor_by_user_id(request.user.id, request.user.email)
        if existing:
            return Response(
                {'error': 'Mentor profile already exists', 'mentor_id': existing['id']},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = MentorProfileSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = serializer.validated_data
            data['user_id'] = request.user.id
            data['is_approved'] = False

            mentor_data = supabase_client.create_mentor_profile(data)
            return Response(mentor_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating mentor profile: {e}")
            return Response(
                {'error': 'Failed to create mentor profile'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['patch', 'put'])
    def update_my_profile(self, request):
        """Update current user's mentor profile"""
        try:
            mentor_data = supabase_client.get_mentor_by_user_id(request.user.id, request.user.email)
            if not mentor_data:
                return Response(
                    {'error': 'Mentor profile not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Fields that can be updated
            allowed_fields = [
                'bio', 'expertise', 'job_title', 'company', 'years_of_experience',
                'linkedin_url', 'timezone', 'languages', 'session_duration',
                'max_mentees', 'available_for_hire', 'hourly_rate'
            ]

            update_data = {k: v for k, v in request.data.items() if k in allowed_fields}

            if not update_data:
                return Response(
                    {'error': 'No valid fields to update'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            expected_version = request.data.get('version', mentor_data.get('version', 1))
            updated = supabase_client.update_mentor_profile(
                mentor_data['id'],
                update_data,
                expected_version
            )

            cache.delete(f'mentor_profile_{mentor_data["id"]}')
            return Response(updated)
        except Exception as e:
            logger.error(f"Error updating mentor profile: {e}")
            if 'version mismatch' in str(e).lower():
                return Response(
                    {'error': 'Profile was updated elsewhere. Please refresh.'},
                    status=status.HTTP_409_CONFLICT
                )
            return Response(
                {'error': 'Failed to update mentor profile'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['patch', 'put'])
    def update_profile(self, request, pk=None):
        """Update mentor profile by ID (must be owner)"""
        try:
            mentor_data = supabase_client._client.table('mentors').select('*').eq('id', pk).single().execute().data
            if not mentor_data or mentor_data['user_id'] != request.user.id:
                return Response(
                    {'error': 'Not authorized to update this profile'},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = MentorProfileSerializer(data=request.data, partial=True)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            expected_version = request.data.get('version', mentor_data['version'])
            updated_data = supabase_client.update_mentor_profile(
                pk,
                serializer.validated_data,
                expected_version
            )

            cache.delete(f'mentor_profile_{pk}')
            return Response(updated_data)
        except Exception as e:
            logger.error(f"Error updating mentor profile {pk}: {e}")
            if 'version mismatch' in str(e).lower():
                return Response(
                    {'error': 'Profile was updated elsewhere. Please refresh.'},
                    status=status.HTTP_409_CONFLICT
                )
            return Response(
                {'error': 'Failed to update mentor profile'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_photo(self, request, pk=None):
        """Upload mentor profile photo"""
        try:
            mentor_data = supabase_client._client.table('mentors').select('*').eq('id', pk).single().execute().data
            if not mentor_data or mentor_data['user_id'] != request.user.id:
                return Response(
                    {'error': 'Not authorized'},
                    status=status.HTTP_403_FORBIDDEN
                )

            photo_file = request.FILES.get('photo')
            if not photo_file:
                return Response(
                    {'error': 'No photo file provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
            if photo_file.content_type not in allowed_types:
                return Response(
                    {'error': 'Invalid file type. Only JPEG, PNG, and WebP allowed'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if photo_file.size > 5 * 1024 * 1024:
                return Response(
                    {'error': 'File too large. Maximum 5MB'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Delete old photo if exists
            if mentor_data.get('photo_url'):
                try:
                    supabase_client.delete_mentor_photo(mentor_data['photo_url'])
                except Exception:
                    pass

            photo_url = supabase_client.upload_mentor_photo(pk, photo_file)
            updated_mentor = supabase_client.update_mentor_profile(
                pk,
                {'photo_url': photo_url},
                mentor_data['version']
            )

            cache.delete(f'mentor_profile_{pk}')
            return Response({
                'photo_url': photo_url,
                'mentor': updated_mentor
            })
        except Exception as e:
            logger.error(f"Error uploading photo: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['delete'])
    def delete_photo(self, request, pk=None):
        """Delete mentor profile photo"""
        try:
            mentor_data = supabase_client._client.table('mentors').select('*').eq('id', pk).single().execute().data
            if not mentor_data or mentor_data['user_id'] != request.user.id:
                return Response(
                    {'error': 'Not authorized'},
                    status=status.HTTP_403_FORBIDDEN
                )

            if not mentor_data.get('photo_url'):
                return Response(
                    {'error': 'No photo to delete'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            supabase_client.delete_mentor_photo(mentor_data['photo_url'])
            supabase_client.update_mentor_profile(
                pk,
                {'photo_url': None},
                mentor_data['version']
            )

            cache.delete(f'mentor_profile_{pk}')
            return Response({'message': 'Photo deleted successfully'})
        except Exception as e:
            logger.error(f"Error deleting photo: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """Get availability slots for a mentor"""
        date_range = {}
        if request.GET.get('start_date'):
            date_range['start_date'] = request.GET.get('start_date')
        if request.GET.get('end_date'):
            date_range['end_date'] = request.GET.get('end_date')

        try:
            slots = supabase_client.get_availability_slots(pk, date_range if date_range else None)

            # Separate by type
            recurring = [s for s in slots if s.get('is_recurring')]
            specific = [s for s in slots if not s.get('is_recurring')]

            return Response({
                'mentor_id': pk,
                'recurring_slots': recurring,
                'specific_date_slots': specific,
                'total_slots': len(slots)
            })
        except Exception as e:
            logger.error(f"Error fetching availability: {e}")
            return Response(
                {'error': 'Failed to fetch availability'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get statistics for current user's mentor profile"""
        try:
            mentor_data = supabase_client.get_mentor_by_user_id(request.user.id, request.user.email)
            if not mentor_data:
                return Response(
                    {'error': 'Mentor profile not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            mentor_id = mentor_data['id']
            bookings = supabase_client.get_mentor_bookings(mentor_id)
            reviews = supabase_client.get_mentor_reviews(mentor_id)
            now = timezone.now()
            today = now.date().isoformat()

            stats = {
                'total_sessions': mentor_data.get('total_sessions', 0),
                'average_rating': float(mentor_data.get('rating', 0)) if mentor_data.get('rating') else 0,
                'total_reviews': len(reviews),
                'pending_bookings': len([b for b in bookings if b.get('status') == 'pending']),
                'upcoming_sessions': len([
                    b for b in bookings
                    if b.get('status') == 'confirmed' and b.get('session_date', '') >= today
                ]),
                'completed_sessions': len([b for b in bookings if b.get('status') == 'completed']),
                'cancelled_sessions': len([b for b in bookings if b.get('status') == 'cancelled']),
                'no_show_sessions': len([b for b in bookings if b.get('status') == 'no_show'])
            }

            return Response(stats)
        except Exception as e:
            logger.error(f"Error fetching mentor stats: {e}")
            return Response(
                {'error': 'Failed to fetch statistics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get reviews for a mentor"""
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))

            reviews = supabase_client.get_mentor_reviews(pk, page=page, page_size=page_size)
            total = supabase_client.get_mentor_review_count(pk)

            return Response({
                'reviews': reviews,
                'count': total,
                'page': page,
                'page_size': page_size
            })
        except Exception as e:
            logger.error(f"Error fetching reviews: {e}")
            return Response(
                {'error': 'Failed to fetch reviews'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _build_cache_key(self, prefix: str, params: dict) -> str:
        param_str = str(sorted(params.items()))
        param_hash = hashlib.md5(param_str.encode()).hexdigest()
        return f'{prefix}_{param_hash}'


class BookingViewSet(viewsets.ViewSet):
    """
    ViewSet for booking operations.

    Endpoints:
    - GET /bookings/ - List bookings (query: role=mentee|mentor, status=pending|confirmed|etc)
    - GET /bookings/{id}/ - Get booking details
    - POST /bookings/ - Create new booking
    - PATCH /bookings/{id}/confirm/ - Confirm booking (mentor)
    - PATCH /bookings/{id}/reject/ - Reject booking (mentor)
    - PATCH /bookings/{id}/cancel/ - Cancel booking (mentee or mentor)
    - PATCH /bookings/{id}/complete/ - Mark session as completed
    - PATCH /bookings/{id}/no_show/ - Mark as no-show
    - PATCH /bookings/{id}/reschedule/ - Reschedule booking
    - PATCH /bookings/{id}/add_meeting_link/ - Add Zoom/Meet link
    - POST /bookings/{id}/add_feedback/ - Add review/feedback
    - PATCH /bookings/{id}/add_notes/ - Add session notes
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [BookingRateThrottle]

    def get_throttles(self):
        if self.action == 'create':
            return [BookingRateThrottle()]
        return []

    def list(self, request):
        """
        List bookings for current user.

        Query params:
        - role: 'mentee' or 'mentor' (default: mentee)
        - status: Filter by status (pending, confirmed, completed, cancelled, no_show)
        - limit: Limit results
        """
        role = request.GET.get('role', 'mentee')
        status_filter = request.GET.get('status')
        limit = request.GET.get('limit')

        try:
            if role == 'mentor':
                mentor_data = supabase_client.get_mentor_by_user_id(request.user.id, request.user.email)
                if not mentor_data:
                    return Response(
                        {'error': 'Mentor profile not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                bookings = supabase_client.get_mentor_bookings(
                    mentor_data['id'],
                    status_filter,
                    limit=int(limit) if limit else None
                )
            else:
                bookings = supabase_client.get_mentee_bookings(
                    request.user.id,
                    status_filter,
                    limit=int(limit) if limit else None
                )

            # Enrich bookings with mentor/mentee info
            enriched_bookings = supabase_client.enrich_bookings(bookings, role)

            return Response({
                'bookings': enriched_bookings,
                'count': len(enriched_bookings),
                'role': role
            })
        except Exception as e:
            logger.error(f"Error listing bookings: {e}")
            return Response(
                {'error': 'Failed to fetch bookings'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, pk=None):
        """Get booking details by ID"""
        try:
            booking = supabase_client.get_booking(pk)
            if not booking:
                return Response(
                    {'error': 'Booking not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Verify user is part of this booking
            mentor = supabase_client.get_mentor_by_user_id(request.user.id, request.user.email)
            is_mentor = mentor and str(mentor['id']) == str(booking.get('mentor_id'))
            is_mentee = booking.get('mentee_id') == request.user.id

            if not is_mentor and not is_mentee:
                return Response(
                    {'error': 'Not authorized to view this booking'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Enrich with mentor and mentee details
            booking = supabase_client.enrich_booking(booking)
            booking['user_role'] = 'mentor' if is_mentor else 'mentee'

            return Response(booking)
        except Exception as e:
            logger.error(f"Error retrieving booking: {e}")
            return Response(
                {'error': 'Failed to fetch booking'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request):
        """Create a new booking with conflict prevention"""
        serializer = BookingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        data['mentee_id'] = request.user.id
        data['status'] = 'pending'

        # Add mentee info
        data['mentee_name'] = f"{request.user.first_name} {request.user.last_name}".strip()
        data['mentee_email'] = request.user.email

        lock_key = f"{data['mentor_id']}_{data['session_date']}_{data['start_time']}"
        lock_id = abs(hash(lock_key)) % (2**31)

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_lock(%s)", [lock_id])

            # Check for conflicts
            conflicts = supabase_client.check_booking_conflicts(
                data['mentor_id'],
                data['session_date'],
                data['start_time'],
                data['end_time']
            )

            if conflicts:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_advisory_unlock(%s)", [lock_id])
                return Response(
                    {'error': 'Time slot is no longer available'},
                    status=status.HTTP_409_CONFLICT
                )

            booking = supabase_client.create_booking(data)

            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_unlock(%s)", [lock_id])

            if booking and booking.get('id'):
                try:
                    send_mentor_booking_notification.delay(str(booking['id']))
                except Exception as e:
                    logger.error(f"Failed to send notification: {e}")

            return Response(booking, status=status.HTTP_201_CREATED)
        except Exception as e:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_advisory_unlock(%s)", [lock_id])
            except:
                pass

            logger.error(f"Error creating booking: {e}")
            return Response(
                {'error': 'Failed to create booking'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['patch'])
    def confirm(self, request, pk=None):
        """Confirm a booking (mentor only)"""
        return self._update_booking_status(request, pk, 'confirmed', mentor_only=True)

    @action(detail=True, methods=['patch'])
    def reject(self, request, pk=None):
        """Reject a booking (mentor only)"""
        reason = request.data.get('reason', '')
        return self._update_booking_status(
            request, pk, 'rejected',
            mentor_only=True,
            extra_data={'rejection_reason': reason}
        )

    @action(detail=True, methods=['patch'])
    def cancel(self, request, pk=None):
        """Cancel a booking (mentee or mentor)"""
        reason = request.data.get('reason', '')
        cancelled_by = 'mentor' if self._is_mentor_for_booking(request.user.id, pk) else 'mentee'
        return self._update_booking_status(
            request, pk, 'cancelled',
            mentor_only=False,
            extra_data={'cancellation_reason': reason, 'cancelled_by': cancelled_by}
        )

    @action(detail=True, methods=['patch'])
    def complete(self, request, pk=None):
        """Mark session as completed (mentor only)"""
        notes = request.data.get('notes', '')
        return self._update_booking_status(
            request, pk, 'completed',
            mentor_only=True,
            extra_data={'session_notes': notes, 'completed_at': timezone.now().isoformat()}
        )

    @action(detail=True, methods=['patch'])
    def no_show(self, request, pk=None):
        """Mark as no-show (mentor only)"""
        who = request.data.get('who', 'mentee')  # mentee or mentor
        return self._update_booking_status(
            request, pk, 'no_show',
            mentor_only=True,
            extra_data={'no_show_by': who}
        )

    @action(detail=True, methods=['patch'])
    def reschedule(self, request, pk=None):
        """Reschedule a booking"""
        new_date = request.data.get('session_date')
        new_start = request.data.get('start_time')
        new_end = request.data.get('end_time')

        if not all([new_date, new_start, new_end]):
            return Response(
                {'error': 'session_date, start_time, and end_time are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            booking = supabase_client.get_booking(pk)
            if not booking:
                return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

            # Verify authorization
            mentor = supabase_client.get_mentor_by_user_id(request.user.id, request.user.email)
            is_mentor = mentor and str(mentor['id']) == str(booking.get('mentor_id'))
            is_mentee = booking.get('mentee_id') == request.user.id

            if not is_mentor and not is_mentee:
                return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

            # Check for conflicts at new time
            conflicts = supabase_client.check_booking_conflicts(
                booking['mentor_id'], new_date, new_start, new_end, exclude_booking_id=pk
            )

            if conflicts:
                return Response(
                    {'error': 'New time slot is not available'},
                    status=status.HTTP_409_CONFLICT
                )

            updated = supabase_client.reschedule_booking(pk, new_date, new_start, new_end)

            # Send notification
            try:
                send_booking_status_update_email.delay(str(pk), 'rescheduled', 'rescheduled')
            except:
                pass

            return Response(updated)
        except Exception as e:
            logger.error(f"Error rescheduling: {e}")
            return Response(
                {'error': 'Failed to reschedule'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['patch'])
    def add_meeting_link(self, request, pk=None):
        """Add or update meeting link (mentor only)"""
        meeting_link = request.data.get('meeting_link', '').strip()
        meeting_platform = request.data.get('meeting_platform', 'zoom')

        if not meeting_link:
            return Response(
                {'error': 'Meeting link is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            booking = supabase_client.get_booking(pk)
            if not booking:
                return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

            mentor = supabase_client.get_mentor_by_user_id(request.user.id, request.user.email)
            if not mentor or str(mentor['id']) != str(booking['mentor_id']):
                return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

            updated = supabase_client.update_booking(pk, {
                'meeting_url': meeting_link,
                'meeting_platform': meeting_platform
            })

            return Response({
                'message': 'Meeting link added successfully',
                'booking': updated
            })
        except Exception as e:
            logger.error(f"Error adding meeting link: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['patch'])
    def add_notes(self, request, pk=None):
        """Add session notes (mentor only)"""
        notes = request.data.get('notes', '').strip()

        try:
            booking = supabase_client.get_booking(pk)
            if not booking:
                return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

            mentor = supabase_client.get_mentor_by_user_id(request.user.id, request.user.email)
            if not mentor or str(mentor['id']) != str(booking['mentor_id']):
                return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

            updated = supabase_client.update_booking(pk, {'session_notes': notes})

            return Response({
                'message': 'Notes added successfully',
                'booking': updated
            })
        except Exception as e:
            logger.error(f"Error adding notes: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def add_feedback(self, request, pk=None):
        """Add rating and feedback after session (mentee only)"""
        rating = request.data.get('rating')
        feedback = request.data.get('feedback', '').strip()

        if not rating or not isinstance(rating, (int, float)) or rating < 1 or rating > 5:
            return Response(
                {'error': 'Rating must be between 1 and 5'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            booking = supabase_client.get_booking(pk)
            if not booking:
                return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

            if booking.get('mentee_id') != request.user.id:
                return Response(
                    {'error': 'Only the mentee can add feedback'},
                    status=status.HTTP_403_FORBIDDEN
                )

            if booking.get('status') != 'completed':
                return Response(
                    {'error': 'Can only add feedback to completed sessions'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if booking.get('rating'):
                return Response(
                    {'error': 'Feedback already submitted'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update booking with feedback
            supabase_client.update_booking(pk, {
                'rating': rating,
                'feedback': feedback,
                'feedback_date': timezone.now().isoformat()
            })

            # Create review record
            review = supabase_client.create_review({
                'mentor_id': booking['mentor_id'],
                'mentee_id': request.user.id,
                'booking_id': pk,
                'rating': rating,
                'comment': feedback,
                'mentee_name': f"{request.user.first_name} {request.user.last_name}".strip()
            })

            # Update mentor's average rating
            supabase_client.update_mentor_rating(booking['mentor_id'])

            return Response({
                'message': 'Feedback submitted successfully',
                'review': review
            })
        except Exception as e:
            logger.error(f"Error adding feedback: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _update_booking_status(self, request, pk, new_status, mentor_only=False, extra_data=None):
        """Helper to update booking status"""
        try:
            booking = supabase_client.get_booking(pk)
            if not booking:
                return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

            mentor = supabase_client.get_mentor_by_user_id(request.user.id, request.user.email)
            is_mentor = mentor and str(mentor['id']) == str(booking.get('mentor_id'))
            is_mentee = booking.get('mentee_id') == request.user.id

            if mentor_only and not is_mentor:
                return Response({'error': 'Only mentor can perform this action'}, status=status.HTTP_403_FORBIDDEN)

            if not mentor_only and not is_mentor and not is_mentee:
                return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

            old_status = booking.get('status')
            update_data = {'status': new_status}
            if extra_data:
                update_data.update(extra_data)

            updated = supabase_client.update_booking(pk, update_data)

            # Update total_sessions if completed
            if new_status == 'completed' and old_status != 'completed':
                supabase_client.increment_mentor_sessions(booking['mentor_id'])

            # Send notification
            try:
                send_booking_status_update_email.delay(str(pk), old_status, new_status)
            except:
                pass

            return Response(updated)
        except Exception as e:
            logger.error(f"Error updating booking status: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _is_mentor_for_booking(self, user_id, booking_id):
        """Check if user is the mentor for a booking"""
        try:
            booking = supabase_client.get_booking(booking_id)
            mentor = supabase_client.get_mentor_by_user_id(user_id)
            return mentor and str(mentor['id']) == str(booking.get('mentor_id'))
        except:
            return False


class AvailabilityViewSet(viewsets.ViewSet):
    """
    ViewSet for mentor availability operations.

    Endpoints:
    - GET /availability/ - List current mentor's availability
    - GET /availability/me/ - Alias for list
    - POST /availability/ - Create availability slot
    - PATCH /availability/{id}/ - Update slot
    - DELETE /availability/{id}/ - Delete slot
    - POST /availability/bulk/ - Create multiple slots at once
    - DELETE /availability/clear/ - Clear all availability
    """
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """List availability for current mentor"""
        try:
            mentor_data = supabase_client.get_mentor_by_user_id(request.user.id, request.user.email)
            if not mentor_data:
                return Response(
                    {'error': 'Mentor profile not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            slots = supabase_client.get_availability_slots(mentor_data['id'])
            recurring = [s for s in slots if s.get('is_recurring')]
            specific = [s for s in slots if not s.get('is_recurring')]

            return Response({
                'recurring_slots': recurring,
                'specific_date_slots': specific,
                'total': len(slots)
            })
        except Exception as e:
            logger.error(f"Error fetching availability: {e}")
            return Response(
                {'error': 'Failed to fetch availability'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='me')
    def my_availability(self, request):
        """Get current mentor's availability"""
        return self.list(request)

    def create(self, request):
        """Create a new availability slot"""
        try:
            mentor_data = supabase_client.get_mentor_by_user_id(request.user.id, request.user.email)
            if not mentor_data:
                return Response(
                    {'error': 'Mentor profile not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            data = request.data.copy()
            data['mentor_id'] = mentor_data['id']
            data['is_active'] = True

            slot = supabase_client.create_availability_slot(data)
            return Response(slot, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating availability slot: {e}")
            return Response(
                {'error': 'Failed to create availability slot'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def bulk(self, request):
        """Create multiple availability slots at once"""
        try:
            mentor_data = supabase_client.get_mentor_by_user_id(request.user.id, request.user.email)
            if not mentor_data:
                return Response(
                    {'error': 'Mentor profile not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            slots_data = request.data.get('slots', [])
            if not slots_data:
                return Response(
                    {'error': 'No slots provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            created_slots = []
            for slot in slots_data:
                slot['mentor_id'] = mentor_data['id']
                slot['is_active'] = True
                created = supabase_client.create_availability_slot(slot)
                if created:
                    created_slots.append(created)

            return Response({
                'created': created_slots,
                'count': len(created_slots)
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating bulk availability: {e}")
            return Response(
                {'error': 'Failed to create availability slots'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def partial_update(self, request, pk=None):
        """Update an availability slot"""
        try:
            mentor_data = supabase_client.get_mentor_by_user_id(request.user.id, request.user.email)
            if not mentor_data:
                return Response(
                    {'error': 'Mentor profile not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            slot = supabase_client.get_availability_slot(pk)
            if not slot or str(slot['mentor_id']) != str(mentor_data['id']):
                return Response(
                    {'error': 'Not authorized'},
                    status=status.HTTP_403_FORBIDDEN
                )

            updated = supabase_client.update_availability_slot(pk, request.data)
            return Response(updated)
        except Exception as e:
            logger.error(f"Error updating availability: {e}")
            return Response(
                {'error': 'Failed to update availability slot'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, pk=None):
        """Delete an availability slot"""
        try:
            mentor_data = supabase_client.get_mentor_by_user_id(request.user.id, request.user.email)
            if not mentor_data:
                return Response(
                    {'error': 'Mentor profile not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            slot = supabase_client.get_availability_slot(pk)
            if not slot or str(slot['mentor_id']) != str(mentor_data['id']):
                return Response(
                    {'error': 'Not authorized'},
                    status=status.HTTP_403_FORBIDDEN
                )

            supabase_client.delete_availability_slot(pk)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting availability: {e}")
            return Response(
                {'error': 'Failed to delete availability slot'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """Clear all availability slots for current mentor"""
        try:
            mentor_data = supabase_client.get_mentor_by_user_id(request.user.id, request.user.email)
            if not mentor_data:
                return Response(
                    {'error': 'Mentor profile not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            slot_type = request.data.get('type', 'all')  # all, recurring, specific
            count = supabase_client.clear_availability_slots(mentor_data['id'], slot_type)

            return Response({
                'message': f'Cleared {count} availability slots',
                'count': count
            })
        except Exception as e:
            logger.error(f"Error clearing availability: {e}")
            return Response(
                {'error': 'Failed to clear availability'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MenteeDashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for mentee-specific operations.

    Endpoints:
    - GET /mentee/dashboard/ - Get mentee dashboard
    - GET /mentee/history/ - Get session history
    - GET /mentee/recommended/ - Get recommended mentors
    - GET /mentee/bookings/ - Get all bookings as mentee
    """
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get mentee dashboard with bookings and recommended mentors"""
        try:
            user_id = request.user.id
            today = timezone.now().date().isoformat()

            # Get bookings
            all_bookings = supabase_client.get_mentee_bookings(user_id)

            pending = [b for b in all_bookings if b.get('status') == 'pending']
            upcoming = [
                b for b in all_bookings
                if b.get('status') == 'confirmed' and b.get('session_date', '') >= today
            ]
            completed = [b for b in all_bookings if b.get('status') == 'completed']

            # Enrich bookings with mentor info
            upcoming = supabase_client.enrich_bookings(upcoming[:5], 'mentee')
            pending = supabase_client.enrich_bookings(pending[:5], 'mentee')

            # Get recommended mentors
            recommended = supabase_client.get_recommended_mentors(user_id, limit=4)

            return Response({
                'user': {
                    'id': user_id,
                    'name': f"{request.user.first_name} {request.user.last_name}".strip(),
                    'email': request.user.email
                },
                'stats': {
                    'total_sessions': len(completed),
                    'upcoming_sessions': len([
                        b for b in all_bookings
                        if b.get('status') == 'confirmed' and b.get('session_date', '') >= today
                    ]),
                    'pending_requests': len(pending)
                },
                'upcoming_sessions': upcoming,
                'pending_bookings': pending,
                'recommended_mentors': recommended
            })
        except Exception as e:
            logger.error(f"Error fetching mentee dashboard: {e}")
            return Response(
                {'error': 'Failed to fetch dashboard'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get session history for mentee"""
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))

            bookings = supabase_client.get_mentee_bookings(
                request.user.id,
                status_filter='completed'
            )

            # Paginate
            start = (page - 1) * page_size
            end = start + page_size
            paginated = bookings[start:end]

            # Enrich with mentor info
            enriched = supabase_client.enrich_bookings(paginated, 'mentee')

            return Response({
                'sessions': enriched,
                'count': len(bookings),
                'page': page,
                'page_size': page_size
            })
        except Exception as e:
            logger.error(f"Error fetching session history: {e}")
            return Response(
                {'error': 'Failed to fetch session history'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def recommended(self, request):
        """Get recommended mentors based on mentee's interests/history"""
        try:
            limit = int(request.GET.get('limit', 6))
            mentors = supabase_client.get_recommended_mentors(request.user.id, limit=limit)

            return Response({
                'mentors': mentors,
                'count': len(mentors)
            })
        except Exception as e:
            logger.error(f"Error fetching recommended mentors: {e}")
            return Response(
                {'error': 'Failed to fetch recommendations'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def bookings(self, request):
        """Get all bookings for current user as mentee"""
        try:
            status_filter = request.GET.get('status')
            bookings = supabase_client.get_mentee_bookings(request.user.id, status_filter)
            enriched = supabase_client.enrich_bookings(bookings, 'mentee')

            return Response({
                'bookings': enriched,
                'count': len(enriched)
            })
        except Exception as e:
            logger.error(f"Error fetching mentee bookings: {e}")
            return Response(
                {'error': 'Failed to fetch bookings'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ExpertiseViewSet(viewsets.ViewSet):
    """ViewSet for expertise categories"""
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        """List all expertise categories"""
        cache_key = 'expertise_categories'
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        try:
            response = supabase_client._client.table('mentorship_expertise').select('*').order('name').execute()
            cache.set(cache_key, response.data, 3600)
            return Response(response.data)
        except Exception as e:
            logger.error(f"Error fetching expertise: {e}")
            return Response(
                {'error': 'Failed to fetch expertise categories'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
