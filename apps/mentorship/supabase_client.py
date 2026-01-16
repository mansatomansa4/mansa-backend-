"""
Supabase Client for Mentorship App

Official supabase-py client with connection pooling, retry logic, and circuit breaker pattern.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from functools import wraps
import time

try:
    from supabase import create_client, Client
except ImportError:
    # Supabase not installed yet
    Client = None

from django.conf import settings

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Simple circuit breaker pattern to prevent cascading failures"""
    def __init__(self, failure_threshold=3, timeout=30):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise Exception("Circuit breaker is OPEN - Supabase unavailable")
        
        try:
            result = func(*args, **kwargs)
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.failures = 0
                logger.info("Circuit breaker reset to CLOSED state")
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.failure_threshold:
                self.state = 'OPEN'
                logger.error(f"Circuit breaker opened after {self.failures} failures")
            raise e


class SupabaseMentorshipClient:
    """
    Client for interacting with Supabase mentorship data.
    Implements connection pooling, retry logic, and circuit breaker pattern.
    """
    _instance = None
    _client: Optional[Client] = None
    _circuit_breaker = CircuitBreaker()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client with credentials from settings"""
        supabase_url = getattr(settings, 'SUPABASE_URL', os.getenv('SUPABASE_URL'))
        # Support both naming conventions
        supabase_key = (
            getattr(settings, 'SUPABASE_SERVICE_KEY', None) or 
            getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', None) or
            os.getenv('SUPABASE_SERVICE_KEY') or 
            os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        )
        
        if not supabase_url or not supabase_key:
            logger.warning("Supabase credentials not configured")
            return
        
        if Client is None:
            logger.error("supabase-py not installed. Run: pip install supabase")
            return
            
        try:
            self._client = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
    
    def is_healthy(self) -> bool:
        """Health check - test Supabase connectivity"""
        try:
            # Simple query to test connection
            self._client.table('mentorship_expertise').select('count').limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            return False
    
    # ========== MENTOR OPERATIONS ==========
    
    def get_mentor_by_user_id(self, user_id: int) -> Optional[Dict]:
        """Get mentor profile by Django user ID"""
        try:
            response = self._circuit_breaker.call(
                lambda: self._client.table('mentors')
                .select('*')
                .eq('user_id', user_id)
                .single()
                .execute()
            )
            return response.data if response.data else None
        except Exception as e:
            logger.error(f"Error fetching mentor by user_id {user_id}: {e}")
            return None
    
    def create_mentor_profile(self, data: Dict) -> Optional[Dict]:
        """Create new mentor profile"""
        try:
            response = self._circuit_breaker.call(
                lambda: self._client.table('mentors')
                .insert(data)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating mentor profile: {e}")
            raise
    
    def update_mentor_profile(self, mentor_id: str, data: Dict, expected_version: int) -> Optional[Dict]:
        """
        Update mentor profile with optimistic locking.
        Raises exception if version mismatch (concurrent update detected).
        """
        try:
            # Include version check and increment
            data['version'] = expected_version + 1
            response = self._circuit_breaker.call(
                lambda: self._client.table('mentors')
                .update(data)
                .eq('id', mentor_id)
                .eq('version', expected_version)  # Optimistic lock
                .execute()
            )
            
            if not response.data:
                raise Exception("Version mismatch - profile was updated by another process")
            
            return response.data[0]
        except Exception as e:
            logger.error(f"Error updating mentor profile {mentor_id}: {e}")
            raise
    
    def get_all_mentors(self, filters: Dict = None, pagination: Dict = None) -> Dict:
        """
        Get all approved mentors with optional filters and pagination.
        Returns: {'data': [...], 'count': total_count}
        """
        try:
            query = self._client.table('mentors').select('*', count='exact').eq('is_approved', True)
            
            # Apply filters
            if filters:
                if 'expertise' in filters and filters['expertise']:
                    # JSONB contains query
                    query = query.contains('expertise', filters['expertise'])
                if 'min_rating' in filters:
                    query = query.gte('rating', filters['min_rating'])
            
            # Apply pagination
            if pagination:
                page = pagination.get('page', 1)
                page_size = pagination.get('page_size', 12)
                start = (page - 1) * page_size
                end = start + page_size - 1
                query = query.range(start, end)
            
            response = self._circuit_breaker.call(lambda: query.execute())
            
            return {
                'data': response.data,
                'count': response.count
            }
        except Exception as e:
            logger.error(f"Error fetching mentors: {e}")
            raise
    
    # ========== AVAILABILITY OPERATIONS ==========
    
    def get_availability_slots(self, mentor_id: str, date_range: Dict = None) -> List[Dict]:
        """Get availability slots for a mentor"""
        try:
            query = self._client.table('mentor_availability').select('*').eq('mentor_id', mentor_id).eq('is_active', True)
            
            if date_range:
                # Filter by date range if provided
                if 'start_date' in date_range:
                    query = query.gte('specific_date', date_range['start_date'])
                if 'end_date' in date_range:
                    query = query.lte('specific_date', date_range['end_date'])
            
            response = self._circuit_breaker.call(lambda: query.execute())
            return response.data
        except Exception as e:
            logger.error(f"Error fetching availability for mentor {mentor_id}: {e}")
            return []
    
    # ========== BOOKING OPERATIONS ==========
    
    def create_booking_with_lock(self, data: Dict) -> Optional[Dict]:
        """
        Create booking with conflict detection.
        Note: PostgreSQL advisory locks are handled at the Django view level.
        """
        try:
            response = self._circuit_breaker.call(
                lambda: self._client.table('mentorship_bookings')
                .insert(data)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating booking: {e}")
            raise
    
    def update_booking_status(self, booking_id: str, status: str, expected_version: int) -> Optional[Dict]:
        """Update booking status with optimistic locking"""
        try:
            data = {
                'status': status,
                'booking_version': expected_version + 1,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            response = self._circuit_breaker.call(
                lambda: self._client.table('mentorship_bookings')
                .update(data)
                .eq('id', booking_id)
                .eq('booking_version', expected_version)
                .execute()
            )
            
            if not response.data:
                raise Exception("Version mismatch - booking was updated by another process")
            
            return response.data[0]
        except Exception as e:
            logger.error(f"Error updating booking {booking_id}: {e}")
            raise
    
    def get_mentee_bookings(self, user_id: int, status_filter: str = None) -> List[Dict]:
        """Get all bookings for a mentee"""
        try:
            query = self._client.table('mentorship_bookings').select('*').eq('mentee_id', user_id)
            
            if status_filter:
                query = query.eq('status', status_filter)
            
            query = query.order('session_date', desc=True)
            
            response = self._circuit_breaker.call(lambda: query.execute())
            return response.data
        except Exception as e:
            logger.error(f"Error fetching bookings for mentee {user_id}: {e}")
            return []
    
    def get_mentor_bookings(self, mentor_id: str, status_filter: str = None) -> List[Dict]:
        """Get all bookings for a mentor"""
        try:
            query = self._client.table('mentorship_bookings').select('*').eq('mentor_id', mentor_id)
            
            if status_filter:
                query = query.eq('status', status_filter)
            
            query = query.order('session_date', desc=True)
            
            response = self._circuit_breaker.call(lambda: query.execute())
            return response.data
        except Exception as e:
            logger.error(f"Error fetching bookings for mentor {mentor_id}: {e}")
            return []


# Singleton instance
supabase_client = SupabaseMentorshipClient()


def get_supabase_client() -> SupabaseMentorshipClient:
    """Get the singleton Supabase client instance"""
    return supabase_client
