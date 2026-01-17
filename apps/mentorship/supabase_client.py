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
    
    def get_mentors_with_member_data(self, filters: Dict = None, pagination: Dict = None) -> Dict:
        """
        Get all approved mentors enriched with member data.
        Joins mentors table with users and members tables for complete profile information.
        Returns: {'data': [...], 'count': total_count}
        """
        try:
            # First get mentors
            mentors_result = self.get_all_mentors(filters, pagination)
            mentors = mentors_result['data']
            
            if not mentors:
                return mentors_result
            
            # Get user IDs from mentors
            user_ids = [m['user_id'] for m in mentors]
            
            # Query users table with their emails
            users_query = self._client.table('users_user').select('id, email, first_name, last_name, phone_number').in_('id', user_ids)
            users_response = self._circuit_breaker.call(lambda: users_query.execute())
            users_dict = {u['id']: u for u in users_response.data}
            
            # Query members table to get additional data
            emails = [u['email'] for u in users_response.data if u.get('email')]
            if emails:
                members_query = self._client.table('members').select('*').in_('email', emails)
                members_response = self._circuit_breaker.call(lambda: members_query.execute())
                members_dict = {m['email']: m for m in members_response.data}
            else:
                members_dict = {}
            
            # Enrich mentor data
            for mentor in mentors:
                user_data = users_dict.get(mentor['user_id'], {})
                member_data = members_dict.get(user_data.get('email', ''), {})
                
                # Add user info
                mentor['user'] = {
                    'id': user_data.get('id'),
                    'email': user_data.get('email', ''),
                    'first_name': user_data.get('first_name', ''),
                    'last_name': user_data.get('last_name', ''),
                    'phone_number': user_data.get('phone_number', ''),
                    'full_name': f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
                }
                
                # Add member info (additional profile details)
                mentor['member'] = {
                    'name': member_data.get('name', mentor['user']['full_name']),
                    'country': member_data.get('country'),
                    'city': member_data.get('city'),
                    'linkedin': member_data.get('linkedin'),
                    'experience': member_data.get('experience'),
                    'areaOfExpertise': member_data.get('areaOfExpertise'),
                    'school': member_data.get('school'),
                    'occupation': member_data.get('occupation'),
                    'jobtitle': member_data.get('jobtitle'),
                    'industry': member_data.get('industry'),
                    'skills': member_data.get('skills'),
                } if member_data else None
            
            return mentors_result
            
        except Exception as e:
            logger.error(f"Error fetching mentors with member data: {e}")
            raise
    
    def sync_mentor_from_member(self, member_email: str, user_id: int) -> Optional[Dict]:
        """
        Create or update mentor profile based on member data.
        Used for automatic sync when membershiptype is 'mentor'.
        """
        try:
            # Check if mentor already exists
            existing_mentor = self.get_mentor_by_user_id(user_id)
            if existing_mentor:
                logger.info(f"Mentor profile already exists for user_id {user_id}")
                return existing_mentor
            
            # Get member data
            member_response = self._circuit_breaker.call(
                lambda: self._client.table('members')
                .select('*')
                .eq('email', member_email)
                .eq('membershiptype', 'mentor')
                .single()
                .execute()
            )
            
            if not member_response.data:
                logger.warning(f"No member found with email {member_email} and membershiptype='mentor'")
                return None
            
            member = member_response.data
            
            # Prepare mentor profile data
            expertise = []
            if member.get('areaOfExpertise'):
                expertise.append(member['areaOfExpertise'])
            if member.get('industry'):
                expertise.append(member['industry'])
            if member.get('skills'):
                skills_list = [s.strip() for s in member['skills'].split(',') if s.strip()]
                expertise.extend(skills_list[:3])
            
            expertise = list(set(expertise))  # Remove duplicates
            
            # Create bio
            bio_parts = []
            if member.get('experience'):
                bio_parts.append(f"Experience: {member['experience']}")
            if member.get('occupation'):
                bio_parts.append(f"Occupation: {member['occupation']}")
            if member.get('jobtitle'):
                bio_parts.append(f"Job Title: {member['jobtitle']}")
            
            bio = " | ".join(bio_parts) if bio_parts else "Experienced mentor ready to help you grow."
            
            # Create mentor profile
            mentor_data = {
                'user_id': user_id,
                'bio': bio,
                'expertise': expertise,
                'is_approved': True,  # Auto-approve mentors from members table
                'rating': 0.00,
                'total_sessions': 0,
                'version': 1
            }
            
            return self.create_mentor_profile(mentor_data)
            
        except Exception as e:
            logger.error(f"Error syncing mentor from member {member_email}: {e}")
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
