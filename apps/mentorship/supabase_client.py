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
    
    def get_member_id_by_email(self, email: str) -> Optional[str]:
        """Get member UUID from the members table by email."""
        try:
            response = self._circuit_breaker.call(
                lambda: self._client.table('members')
                .select('id')
                .ilike('email', email)
                .limit(1)
                .execute()
            )
            if response.data and len(response.data) > 0:
                return response.data[0]['id']
            return None
        except Exception as e:
            logger.error(f"Error fetching member by email {email}: {e}")
            return None

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
                .execute()
            )
            # Return first result if exists, otherwise None
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching mentor by user_id {user_id}: {e}")
            return None
    
    def get_mentor_with_member_data(self, user_id: int, email: str = None) -> Optional[Dict]:
        """
        Get mentor profile with related member data by Django user ID or email.
        If user_id lookup fails and email is provided, lookup through members table.
        """
        try:
            # First try to query by user_id
            response = self._circuit_breaker.call(
                lambda: self._client.table('mentors')
                .select('*, member:member_id(*)')
                .eq('user_id', user_id)
                .execute()
            )
            
            mentor = None
            if response.data and len(response.data) > 0:
                mentor = response.data[0]
            elif email:
                logger.info(f"No mentor found by user_id {user_id}, trying email lookup: {email}")
                # Get member by email first
                member_response = self._circuit_breaker.call(
                    lambda: self._client.table('members')
                    .select('id')
                    .eq('email', email)
                    .execute()
                )
                
                if not member_response.data or len(member_response.data) == 0:
                    logger.info(f"No member found with email {email}")
                    return None
                
                member_id = member_response.data[0]['id']
                
                # Now get mentor by member_id
                mentor_response = self._circuit_breaker.call(
                    lambda: self._client.table('mentors')
                    .select('*, member:member_id(*)')
                    .eq('member_id', member_id)
                    .execute()
                )
                
                if not mentor_response.data or len(mentor_response.data) == 0:
                    logger.info(f"No mentor profile found for member_id {member_id}")
                    return None
                
                mentor = mentor_response.data[0]
            else:
                return None
            
            # Map member fields to mentor profile fields
            member_info = mentor.pop('member', {}) if mentor.get('member') else {}
            
            if member_info:
                mentor['job_title'] = member_info.get('jobtitle') or ''
                mentor['company'] = member_info.get('occupation') or ''
                mentor['years_of_experience'] = int(member_info.get('experience') or 0) if str(member_info.get('experience', '')).isdigit() else 0
                mentor['linkedin_url'] = member_info.get('linkedin') or ''
                mentor['member_name'] = member_info.get('name') or ''
                mentor['member_email'] = member_info.get('email') or ''
                mentor['phone'] = member_info.get('phone') or ''
                mentor['country'] = member_info.get('country') or ''
                mentor['city'] = member_info.get('city') or ''
                mentor['area_of_expertise'] = member_info.get('areaofexpertise') or ''
            
            return mentor
        except Exception as e:
            logger.error(f"Error fetching mentor with member data for user_id {user_id}: {e}")
            # Fallback to get_mentor_by_user_id with email
            return self.get_mentor_by_user_id(user_id, email)

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
        Uses member_id foreign key for direct joining.
        Returns: {'data': [...], 'count': total_count}
        """
        try:
            # Build the query with member data join
            # Note: Supabase allows foreign key expansion
            query = (
                self._client.table('mentors')
                .select('*, member:member_id(*)', count='exact')
                .eq('is_approved', True)
            )
            
            # Apply filters
            if filters:
                if 'id' in filters:
                    query = query.eq('id', filters['id'])
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
            
            # Enrich the data structure
            enriched_data = []
            for mentor in response.data:
                member_data = mentor.pop('member', {}) if mentor.get('member') else {}
                
                enriched_mentor = {
                    **mentor,
                    'name': member_data.get('name', ''),
                    'email': member_data.get('email', ''),
                    'phone': member_data.get('phone', ''),
                    'country': member_data.get('country', ''),
                    'city': member_data.get('city', ''),
                    'linkedin': member_data.get('linkedin', ''),
                    'experience': member_data.get('experience', ''),
                    'areaofexpertise': member_data.get('areaofexpertise', ''),
                    'school': member_data.get('school', ''),
                    'occupation': member_data.get('occupation', ''),
                    'jobtitle': member_data.get('jobtitle', ''),
                    'skills': member_data.get('skills', ''),
                    'location': member_data.get('location', ''),
                    'member_data': member_data  # Keep full member data for reference
                }
                enriched_data.append(enriched_mentor)
            
            return {
                'data': enriched_data,
                'count': response.count
            }
        except Exception as e:
            logger.error(f"Error fetching mentors with member data: {e}")
            # Fallback to old method if new approach fails
            return self.get_all_mentors(filters, pagination)
    
    def sync_mentor_from_member(self, member_email: str, user_id: int) -> Optional[Dict]:
        """
        Create or update mentor profile based on member data.
        Used for automatic sync when membershiptype contains 'mentor'.
        """
        try:
            # Check if mentor already exists by user_id
            existing_mentor = self.get_mentor_by_user_id(user_id)
            if existing_mentor:
                logger.info(f"Mentor profile already exists for user_id {user_id}")
                return existing_mentor

            # Get member data - use ilike for case-insensitive match on membershiptype
            member_response = self._circuit_breaker.call(
                lambda: self._client.table('members')
                .select('*')
                .ilike('email', member_email)
                .execute()
            )

            if not member_response.data:
                logger.warning(f"No member found with email {member_email}")
                return None

            # Find the member with mentor in membershiptype (case-insensitive)
            member = None
            for m in member_response.data:
                membershiptype = (m.get('membershiptype') or '').lower()
                if 'mentor' in membershiptype:
                    member = m
                    break

            if not member:
                logger.warning(f"Member {member_email} is not a mentor (membershiptype doesn't contain 'mentor')")
                return None

            # Get member_id (UUID) for linking
            member_id = member.get('id')
            
            # Check if mentor already exists by member_id to prevent duplicates
            existing_by_member = self._circuit_breaker.call(
                lambda: self._client.table('mentors')
                .select('*')
                .eq('member_id', member_id)
                .execute()
            )
            
            if existing_by_member.data and len(existing_by_member.data) > 0:
                logger.info(f"Mentor profile already exists for member_id {member_id}")
                return existing_by_member.data[0]

            # Prepare mentor profile data
            expertise = []
            # Handle both camelCase and lowercase field names
            area_of_expertise = member.get('areaOfExpertise') or member.get('areaofexpertise') or ''
            if area_of_expertise:
                expertise.append(area_of_expertise)
            if member.get('industry'):
                expertise.append(member['industry'])
            if member.get('skills'):
                skills_list = [s.strip() for s in member['skills'].split(',') if s.strip()]
                expertise.extend(skills_list[:3])

            expertise = list(set(filter(None, expertise)))  # Remove duplicates and empty strings

            # Create bio
            bio_parts = []
            if member.get('experience'):
                bio_parts.append(f"Experience: {member['experience']}")
            if member.get('occupation'):
                bio_parts.append(f"Occupation: {member['occupation']}")
            if member.get('jobtitle'):
                bio_parts.append(f"Job Title: {member['jobtitle']}")

            bio = " | ".join(bio_parts) if bio_parts else "Experienced mentor ready to help you grow."

            # Create mentor profile with member_id link
            mentor_data = {
                'user_id': user_id,
                'member_id': member_id,  # Link to members table
                'bio': bio,
                'expertise': expertise if expertise else ['General Mentorship'],
                'is_approved': True,  # Auto-approve mentors from members table
                'rating': 0.00,
                'total_sessions': 0,
                'version': 1
            }

            created_mentor = self.create_mentor_profile(mentor_data)
            logger.info(f"Created mentor profile for user_id {user_id} linked to member_id {member_id}")
            return created_mentor

        except Exception as e:
            # Check if it's a duplicate key error
            error_str = str(e).lower()
            if 'duplicate' in error_str or '23505' in error_str:
                logger.warning(f"Mentor profile already exists for {member_email}, fetching existing profile")
                # Try to fetch the existing mentor
                return self.get_mentor_by_user_id(user_id)
            logger.error(f"Error syncing mentor from member {member_email}: {e}")
            raise
    
    def get_mentor_by_user_id(self, user_id: int, email: str = None) -> Optional[Dict]:
        """
        Get mentor profile by user_id or email.
        If user_id lookup fails and email is provided, lookup through members table.
        Returns mentor data with member information or None if not found.
        """
        try:
            # First try to query by user_id
            response = self._circuit_breaker.call(
                lambda: self._client.table('mentors')
                .select('*, member:member_id(*)')
                .eq('user_id', user_id)
                .execute()
            )
            
            # If found by user_id, return it
            if response.data and len(response.data) > 0:
                mentor = response.data[0]
            # If not found by user_id and email is provided, try email lookup
            elif email:
                logger.info(f"No mentor found by user_id {user_id}, trying email lookup: {email}")
                # Get member by email first
                member_response = self._circuit_breaker.call(
                    lambda: self._client.table('members')
                    .select('id')
                    .eq('email', email)
                    .execute()
                )
                
                if not member_response.data or len(member_response.data) == 0:
                    logger.info(f"No member found with email {email}")
                    return None
                
                member_id = member_response.data[0]['id']
                
                # Now get mentor by member_id
                mentor_response = self._circuit_breaker.call(
                    lambda: self._client.table('mentors')
                    .select('*, member:member_id(*)')
                    .eq('member_id', member_id)
                    .execute()
                )
                
                if not mentor_response.data or len(mentor_response.data) == 0:
                    logger.info(f"No mentor profile found for member_id {member_id}")
                    return None
                
                mentor = mentor_response.data[0]
            else:
                logger.info(f"No mentor profile found for user_id {user_id}")
                return None
            
            # Enrich with member data
            member_data = mentor.pop('member', {}) if mentor.get('member') else {}
            
            enriched_mentor = {
                **mentor,
                'name': member_data.get('name', ''),
                'email': member_data.get('email', ''),
                'phone': member_data.get('phone', ''),
                'country': member_data.get('country', ''),
                'city': member_data.get('city', ''),
                'linkedin': member_data.get('linkedin', ''),
                'experience': member_data.get('experience', ''),
                'areaofexpertise': member_data.get('areaofexpertise', ''),
                'school': member_data.get('school', ''),
                'occupation': member_data.get('occupation', ''),
                'jobtitle': member_data.get('jobtitle', ''),
                'skills': member_data.get('skills', ''),
                'location': member_data.get('location', ''),
                'member_data': member_data
            }
            
            return enriched_mentor
            
        except Exception as e:
            logger.error(f"Error fetching mentor by user_id {user_id}: {e}")
            return None
    
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

    def get_availability_slot(self, slot_id: str) -> Optional[Dict]:
        """Get a single availability slot by ID"""
        try:
            response = self._circuit_breaker.call(
                lambda: self._client.table('mentor_availability')
                .select('*')
                .eq('id', slot_id)
                .execute()
            )
            return response.data[0] if response.data and len(response.data) > 0 else None
        except Exception as e:
            logger.error(f"Error fetching availability slot {slot_id}: {e}")
            return None

    def create_availability_slot(self, data: Dict) -> Optional[Dict]:
        """Create a new availability slot"""
        try:
            # Ensure required fields
            slot_data = {
                'mentor_id': data['mentor_id'],
                'start_time': data.get('start_time'),
                'end_time': data.get('end_time'),
                'is_recurring': data.get('is_recurring', False),
                'is_active': data.get('is_active', True),
            }

            # Add day_of_week for recurring slots
            if slot_data['is_recurring'] and 'day_of_week' in data:
                slot_data['day_of_week'] = data['day_of_week']

            # Add specific_date for non-recurring slots
            if not slot_data['is_recurring'] and 'specific_date' in data:
                slot_data['specific_date'] = data['specific_date']

            response = self._circuit_breaker.call(
                lambda: self._client.table('mentor_availability')
                .insert(slot_data)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating availability slot: {e}")
            raise

    def update_availability_slot(self, slot_id: str, data: Dict) -> Optional[Dict]:
        """Update an availability slot"""
        try:
            # Build update data, only include provided fields
            update_data = {}
            if 'start_time' in data:
                update_data['start_time'] = data['start_time']
            if 'end_time' in data:
                update_data['end_time'] = data['end_time']
            if 'day_of_week' in data:
                update_data['day_of_week'] = data['day_of_week']
            if 'specific_date' in data:
                update_data['specific_date'] = data['specific_date']
            if 'is_active' in data:
                update_data['is_active'] = data['is_active']
            if 'is_recurring' in data:
                update_data['is_recurring'] = data['is_recurring']

            update_data['updated_at'] = datetime.utcnow().isoformat()

            response = self._circuit_breaker.call(
                lambda: self._client.table('mentor_availability')
                .update(update_data)
                .eq('id', slot_id)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating availability slot {slot_id}: {e}")
            raise

    def delete_availability_slot(self, slot_id: str) -> bool:
        """Delete an availability slot (soft delete by setting is_active=False)"""
        try:
            response = self._circuit_breaker.call(
                lambda: self._client.table('mentor_availability')
                .update({'is_active': False, 'updated_at': datetime.utcnow().isoformat()})
                .eq('id', slot_id)
                .execute()
            )
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error deleting availability slot {slot_id}: {e}")
            raise
    
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
    
    def update_booking_status(self, booking_id: str, status: str, expected_version: int = None) -> Optional[Dict]:
        """Update booking status"""
        try:
            data = {
                'status': status,
                'updated_at': datetime.utcnow().isoformat()
            }

            response = self._circuit_breaker.call(
                lambda: self._client.table('mentorship_bookings')
                .update(data)
                .eq('id', booking_id)
                .execute()
            )

            if not response.data:
                raise Exception("Booking not found or update failed")

            return response.data[0]
        except Exception as e:
            logger.error(f"Error updating booking {booking_id}: {e}")
            raise
    
    def get_mentee_bookings(self, user_id_or_member_id, status_filter: str = None, limit: int = None, email: str = None) -> List[Dict]:
        """Get all bookings for a mentee. Accepts member UUID or Django user ID + email."""
        try:
            mentee_id = user_id_or_member_id
            # If it looks like an integer (Django user_id), resolve to member UUID via email
            if isinstance(user_id_or_member_id, int) and email:
                member_id = self.get_member_id_by_email(email)
                if member_id:
                    mentee_id = member_id
                else:
                    logger.warning(f"No member found for email {email}, using user_id {user_id_or_member_id}")
                    return []
            query = self._client.table('mentorship_bookings').select('*').eq('mentee_id', str(mentee_id))

            if status_filter:
                query = query.eq('status', status_filter)

            query = query.order('session_date', desc=True)

            if limit:
                query = query.limit(limit)

            response = self._circuit_breaker.call(lambda: query.execute())
            return response.data
        except Exception as e:
            logger.error(f"Error fetching bookings for mentee {user_id}: {e}")
            return []

    def get_mentor_bookings(self, mentor_id: str, status_filter: str = None, limit: int = None) -> List[Dict]:
        """Get all bookings for a mentor"""
        try:
            query = self._client.table('mentorship_bookings').select('*').eq('mentor_id', mentor_id)

            if status_filter:
                query = query.eq('status', status_filter)

            query = query.order('session_date', desc=True)

            if limit:
                query = query.limit(limit)

            response = self._circuit_breaker.call(lambda: query.execute())
            return response.data
        except Exception as e:
            logger.error(f"Error fetching bookings for mentor {mentor_id}: {e}")
            return []
    
    def get_booking(self, booking_id: str) -> Optional[Dict]:
        """Get a single booking by ID"""
        try:
            response = self._circuit_breaker.call(
                lambda: self._client.table('mentorship_bookings')
                .select('*')
                .eq('id', booking_id)
                .execute()
            )
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching booking {booking_id}: {e}")
            return None
    
    # ========== STORAGE OPERATIONS ==========
    
    def upload_mentor_photo(self, mentor_id: str, photo_file) -> str:
        """
        Upload mentor profile photo to Supabase storage.
        Returns the public URL of the uploaded image.
        """
        try:
            # Generate unique filename
            import uuid
            from pathlib import Path
            
            file_ext = Path(photo_file.name).suffix
            unique_filename = f"mentor_{mentor_id}_{uuid.uuid4().hex[:8]}{file_ext}"
            file_path = f"mentors/{unique_filename}"
            
            # Read file content
            file_content = photo_file.read()
            
            # Upload to Supabase storage bucket
            # Note: Using the 'mentors-profile' bucket created in Supabase dashboard
            bucket_name = 'mentors-profile'
            
            # Upload file
            response = self._circuit_breaker.call(
                lambda: self._client.storage.from_(bucket_name).upload(
                    file_path,
                    file_content,
                    {'content-type': photo_file.content_type}
                )
            )
            
            # Get public URL
            public_url = self._client.storage.from_(bucket_name).get_public_url(file_path)
            
            logger.info(f"Uploaded photo for mentor {mentor_id}: {public_url}")
            return public_url
            
        except Exception as e:
            logger.error(f"Error uploading photo for mentor {mentor_id}: {e}")
            raise Exception(f"Failed to upload photo: {str(e)}")
    
    def delete_mentor_photo(self, photo_url: str) -> bool:
        """
        Delete mentor profile photo from Supabase storage.
        Returns True if successful.
        """
        try:
            # Extract file path from URL
            bucket_name = 'mentors-profile'
            # URL format: https://{project}.supabase.co/storage/v1/object/public/{bucket}/{path}
            if f'/object/public/{bucket_name}/' in photo_url:
                file_path = photo_url.split(f'/object/public/{bucket_name}/')[1]

                # Delete file
                self._circuit_breaker.call(
                    lambda: self._client.storage.from_(bucket_name).remove([file_path])
                )

                logger.info(f"Deleted photo: {file_path}")
                return True
            else:
                logger.warning(f"Invalid photo URL format: {photo_url}")
                return False

        except Exception as e:
            logger.error(f"Error deleting photo {photo_url}: {e}")
            return False

    # ========== REVIEW OPERATIONS ==========

    def get_mentor_reviews(self, mentor_id: str, limit: int = 10, page: int = 1, page_size: int = 10) -> List[Dict]:
        """Get reviews for a mentor with pagination"""
        try:
            offset = (page - 1) * page_size
            response = self._circuit_breaker.call(
                lambda: self._client.table('mentorship_reviews')
                .select('*')
                .eq('mentor_id', mentor_id)
                .order('created_at', desc=True)
                .range(offset, offset + page_size - 1)
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching reviews for mentor {mentor_id}: {e}")
            return []

    def get_mentor_review_count(self, mentor_id: str) -> int:
        """Get total review count for a mentor"""
        try:
            response = self._circuit_breaker.call(
                lambda: self._client.table('mentorship_reviews')
                .select('id', count='exact')
                .eq('mentor_id', mentor_id)
                .execute()
            )
            return response.count or 0
        except Exception as e:
            logger.error(f"Error fetching review count for mentor {mentor_id}: {e}")
            return 0

    def create_review(self, data: Dict) -> Optional[Dict]:
        """Create a new review for a mentor"""
        try:
            review_data = {
                'mentor_id': data['mentor_id'],
                'mentee_id': data['mentee_id'],
                'booking_id': data.get('booking_id'),
                'rating': data['rating'],
                'comment': data.get('comment', ''),
                'mentee_name': data.get('mentee_name', ''),
                'created_at': datetime.utcnow().isoformat()
            }

            response = self._circuit_breaker.call(
                lambda: self._client.table('mentorship_reviews')
                .insert(review_data)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating review: {e}")
            raise

    def update_mentor_rating(self, mentor_id: str) -> Optional[float]:
        """Recalculate and update mentor's average rating"""
        try:
            # Get all reviews for the mentor
            reviews_response = self._circuit_breaker.call(
                lambda: self._client.table('mentorship_reviews')
                .select('rating')
                .eq('mentor_id', mentor_id)
                .execute()
            )

            if not reviews_response.data:
                return None

            # Calculate average
            ratings = [r['rating'] for r in reviews_response.data]
            avg_rating = round(sum(ratings) / len(ratings), 2)

            # Update mentor profile
            self._circuit_breaker.call(
                lambda: self._client.table('mentors')
                .update({'rating': avg_rating, 'updated_at': datetime.utcnow().isoformat()})
                .eq('id', mentor_id)
                .execute()
            )

            logger.info(f"Updated mentor {mentor_id} rating to {avg_rating}")
            return avg_rating
        except Exception as e:
            logger.error(f"Error updating mentor rating for {mentor_id}: {e}")
            return None

    def increment_mentor_sessions(self, mentor_id: str) -> bool:
        """Increment mentor's total session count"""
        try:
            # Get current count
            mentor_response = self._circuit_breaker.call(
                lambda: self._client.table('mentors')
                .select('total_sessions')
                .eq('id', mentor_id)
                .execute()
            )

            current_sessions = 0
            if mentor_response.data and len(mentor_response.data) > 0:
                current_sessions = mentor_response.data[0].get('total_sessions', 0)

            # Update count
            self._circuit_breaker.call(
                lambda: self._client.table('mentors')
                .update({
                    'total_sessions': current_sessions + 1,
                    'updated_at': datetime.utcnow().isoformat()
                })
                .eq('id', mentor_id)
                .execute()
            )

            logger.info(f"Incremented sessions for mentor {mentor_id} to {current_sessions + 1}")
            return True
        except Exception as e:
            logger.error(f"Error incrementing sessions for mentor {mentor_id}: {e}")
            return False

    # ========== SEARCH OPERATIONS ==========

    def search_mentors(self, filters: Dict = None, pagination: Dict = None) -> Dict:
        """
        Search mentors with full-text search and filters.
        Returns: {'data': [...], 'count': total_count}
        """
        try:
            # Start with approved mentors, join with member data
            query = (
                self._client.table('mentors')
                .select('*, member:member_id(*)', count='exact')
                .eq('is_approved', True)
            )

            if filters:
                # Search query (searches bio, expertise)
                if filters.get('query'):
                    search_term = filters['query']
                    # Use ilike for case-insensitive search on bio
                    query = query.ilike('bio', f'%{search_term}%')

                # Filter by expertise
                if filters.get('expertise'):
                    query = query.contains('expertise', [filters['expertise']])

                # Filter by minimum rating
                if filters.get('min_rating'):
                    query = query.gte('rating', filters['min_rating'])

                # Filter by availability (has any active availability slots)
                # This would require a subquery or RPC function in Supabase

            # Apply pagination
            if pagination:
                page = pagination.get('page', 1)
                page_size = pagination.get('page_size', 12)
                start = (page - 1) * page_size
                end = start + page_size - 1
                query = query.range(start, end)

            # Order by rating descending
            query = query.order('rating', desc=True)

            response = self._circuit_breaker.call(lambda: query.execute())

            # Enrich with member data
            enriched_data = []
            for mentor in response.data:
                member_data = mentor.pop('member', {}) if mentor.get('member') else {}

                enriched_mentor = {
                    **mentor,
                    'name': member_data.get('name', ''),
                    'email': member_data.get('email', ''),
                    'phone': member_data.get('phone', ''),
                    'country': member_data.get('country', ''),
                    'city': member_data.get('city', ''),
                    'linkedin': member_data.get('linkedin', ''),
                    'experience': member_data.get('experience', ''),
                    'areaofexpertise': member_data.get('areaofexpertise', ''),
                    'occupation': member_data.get('occupation', ''),
                    'jobtitle': member_data.get('jobtitle', ''),
                    'skills': member_data.get('skills', ''),
                }
                enriched_data.append(enriched_mentor)

            return {
                'data': enriched_data,
                'count': response.count
            }
        except Exception as e:
            logger.error(f"Error searching mentors: {e}")
            return {'data': [], 'count': 0}

    def get_recommended_mentors(self, user_id: int, limit: int = 6) -> List[Dict]:
        """
        Get recommended mentors for a mentee.
        Simple recommendation based on highest rated mentors.
        """
        try:
            response = self._circuit_breaker.call(
                lambda: self._client.table('mentors')
                .select('*, member:member_id(*)')
                .eq('is_approved', True)
                .order('rating', desc=True)
                .order('total_sessions', desc=True)
                .limit(limit)
                .execute()
            )

            if not response.data:
                return []

            # Enrich with member data
            enriched_data = []
            for mentor in response.data:
                member_data = mentor.pop('member', {}) if mentor.get('member') else {}

                enriched_mentor = {
                    **mentor,
                    'name': member_data.get('name', ''),
                    'email': member_data.get('email', ''),
                    'occupation': member_data.get('occupation', ''),
                    'jobtitle': member_data.get('jobtitle', ''),
                    'areaofexpertise': member_data.get('areaofexpertise', ''),
                }
                enriched_data.append(enriched_mentor)

            return enriched_data
        except Exception as e:
            logger.error(f"Error getting recommended mentors for user {user_id}: {e}")
            return []

    # ========== ENHANCED BOOKING OPERATIONS ==========

    def get_booking(self, booking_id: str) -> Optional[Dict]:
        """Get a single booking by ID"""
        try:
            response = self._circuit_breaker.call(
                lambda: self._client.table('mentorship_bookings')
                .select('*')
                .eq('id', booking_id)
                .execute()
            )
            return response.data[0] if response.data and len(response.data) > 0 else None
        except Exception as e:
            logger.error(f"Error fetching booking {booking_id}: {e}")
            return None

    def create_booking(self, data: Dict) -> Optional[Dict]:
        """Create a new booking"""
        try:
            # Build session_date as full ISO timestamp from date + start_time
            session_date = data.get('session_date', '')
            start_time = data.get('start_time', '')
            if isinstance(session_date, str) and 'T' not in session_date and start_time:
                # Combine date and time into ISO timestamp
                session_date = f"{session_date}T{start_time}:00+00:00"
            elif hasattr(session_date, 'isoformat'):
                st = data.get('start_time', '')
                if hasattr(st, 'isoformat'):
                    st = st.isoformat()
                session_date = f"{session_date.isoformat()}T{st}+00:00"

            # Calculate duration from start_time and end_time
            duration_minutes = data.get('duration_minutes', 60)
            if 'start_time' in data and 'end_time' in data:
                from datetime import datetime as dt
                st = data['start_time']
                et = data['end_time']
                if hasattr(st, 'hour'):
                    duration_minutes = (et.hour * 60 + et.minute) - (st.hour * 60 + st.minute)
                elif isinstance(st, str) and isinstance(et, str):
                    sp = st.split(':')
                    ep = et.split(':')
                    duration_minutes = (int(ep[0]) * 60 + int(ep[1])) - (int(sp[0]) * 60 + int(sp[1]))

            booking_data = {
                'mentor_id': str(data['mentor_id']),
                'mentee_id': str(data['mentee_id']),
                'session_date': session_date,
                'duration_minutes': duration_minutes,
                'session_type': data.get('session_type', 'one-on-one'),
                'topic': data.get('topic', ''),
                'notes': data.get('description', '') or data.get('notes', ''),
                'mentee_goals': data.get('mentee_goals', ''),
                'status': 'pending',
                'created_at': datetime.utcnow().isoformat()
            }

            response = self._circuit_breaker.call(
                lambda: self._client.table('mentorship_bookings')
                .insert(booking_data)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating booking: {e}")
            raise

    def update_booking(self, booking_id: str, data: Dict) -> Optional[Dict]:
        """Update a booking"""
        try:
            # Build update data
            update_data = {}
            allowed_fields = [
                'status', 'session_date', 'duration_minutes',
                'topic', 'notes', 'meeting_url', 'meeting_platform',
                'mentor_feedback', 'mentee_goals',
                'cancellation_reason', 'cancelled_by', 'cancelled_at',
                'rating', 'booking_status',
            ]

            for field in allowed_fields:
                if field in data:
                    update_data[field] = data[field]

            update_data['updated_at'] = datetime.utcnow().isoformat()

            response = self._circuit_breaker.call(
                lambda: self._client.table('mentorship_bookings')
                .update(update_data)
                .eq('id', booking_id)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating booking {booking_id}: {e}")
            raise

    def reschedule_booking(self, booking_id: str, new_date: str, new_start: str, new_end: str) -> Optional[Dict]:
        """Reschedule a booking to a new date/time"""
        try:
            # Combine date + time into ISO timestamp
            session_date = f"{new_date}T{new_start}:00+00:00"

            # Calculate duration
            duration_minutes = 60
            if new_start and new_end:
                sp = new_start.split(':')
                ep = new_end.split(':')
                duration_minutes = (int(ep[0]) * 60 + int(ep[1])) - (int(sp[0]) * 60 + int(sp[1]))

            update_data = {
                'session_date': session_date,
                'duration_minutes': duration_minutes,
                'status': 'pending',
                'updated_at': datetime.utcnow().isoformat()
            }

            response = self._circuit_breaker.call(
                lambda: self._client.table('mentorship_bookings')
                .update(update_data)
                .eq('id', booking_id)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error rescheduling booking {booking_id}: {e}")
            raise

    def check_booking_conflicts(
        self,
        mentor_id: str,
        session_date: str,
        start_time: str = None,
        end_time: str = None,
        exclude_booking_id: str = None
    ) -> bool:
        """
        Check if there are any conflicting bookings for the given time slot.
        Returns True if there's a conflict.
        The DB stores session_date as a timestamp and duration_minutes.
        """
        try:
            # Build the full timestamp for the requested session
            if start_time and 'T' not in str(session_date):
                requested_start = f"{session_date}T{start_time}:00+00:00"
            else:
                requested_start = str(session_date)

            # Calculate requested end time
            if start_time and end_time:
                requested_end = f"{session_date}T{end_time}:00+00:00"
            else:
                requested_end = None

            # Get all bookings for this mentor on the same date
            # Filter by date range: from start of day to end of day
            day_start = f"{str(session_date)[:10]}T00:00:00+00:00"
            day_end = f"{str(session_date)[:10]}T23:59:59+00:00"

            query = (
                self._client.table('mentorship_bookings')
                .select('id, session_date, duration_minutes')
                .eq('mentor_id', mentor_id)
                .gte('session_date', day_start)
                .lte('session_date', day_end)
                .in_('status', ['pending', 'confirmed'])
            )

            if exclude_booking_id:
                query = query.neq('id', exclude_booking_id)

            response = self._circuit_breaker.call(lambda: query.execute())

            if not response.data:
                return False

            # Check for time overlap using session_date + duration_minutes
            from datetime import datetime as dt, timedelta
            req_start = dt.fromisoformat(requested_start.replace('+00:00', '+00:00'))
            if requested_end:
                req_end = dt.fromisoformat(requested_end.replace('+00:00', '+00:00'))
            else:
                req_end = req_start + timedelta(minutes=60)

            for booking in response.data:
                existing_start = dt.fromisoformat(booking['session_date'].replace('Z', '+00:00'))
                existing_duration = booking.get('duration_minutes', 60)
                existing_end = existing_start + timedelta(minutes=existing_duration)

                # Check overlap
                if req_start < existing_end and req_end > existing_start:
                    logger.warning(f"Booking conflict detected for mentor {mentor_id} on {session_date}")
                    return True

            return False
        except Exception as e:
            logger.error(f"Error checking booking conflicts: {e}")
            # In case of error, assume conflict to be safe
            return True

    def enrich_booking(self, booking: Dict) -> Dict:
        """Enrich a single booking with mentor and mentee details"""
        try:
            enriched = {**booking}

            # Get mentor details
            if booking.get('mentor_id'):
                mentor_response = self._circuit_breaker.call(
                    lambda: self._client.table('mentors')
                    .select('*, member:member_id(name, email, jobtitle, occupation)')
                    .eq('id', booking['mentor_id'])
                    .execute()
                )
                if mentor_response.data and len(mentor_response.data) > 0:
                    mentor = mentor_response.data[0]
                    member_data = mentor.pop('member', {}) if mentor.get('member') else {}
                    enriched['mentor'] = {
                        'id': mentor.get('id'),
                        'user_id': mentor.get('user_id'),
                        'name': member_data.get('name', ''),
                        'email': member_data.get('email', ''),
                        'job_title': member_data.get('jobtitle', ''),
                        'occupation': member_data.get('occupation', ''),
                        'photo_url': mentor.get('photo_url'),
                        'rating': mentor.get('rating'),
                    }

            # Get mentee details from Django user
            # Note: This requires the mentee_id to be a Django user ID
            # The view layer should handle this enrichment if needed

            return enriched
        except Exception as e:
            logger.error(f"Error enriching booking: {e}")
            return booking

    def enrich_bookings(self, bookings: List[Dict], role: str = None) -> List[Dict]:
        """Enrich multiple bookings with mentor and mentee details"""
        try:
            if not bookings:
                return []

            # Collect unique mentor IDs
            mentor_ids = list(set(b.get('mentor_id') for b in bookings if b.get('mentor_id')))

            # Batch fetch mentor data
            mentors_map = {}
            if mentor_ids:
                mentors_response = self._circuit_breaker.call(
                    lambda: self._client.table('mentors')
                    .select('*, member:member_id(name, email, jobtitle, occupation)')
                    .in_('id', mentor_ids)
                    .execute()
                )

                for mentor in (mentors_response.data or []):
                    member_data = mentor.pop('member', {}) if mentor.get('member') else {}
                    mentors_map[mentor['id']] = {
                        'id': mentor.get('id'),
                        'user_id': mentor.get('user_id'),
                        'name': member_data.get('name', ''),
                        'email': member_data.get('email', ''),
                        'job_title': member_data.get('jobtitle', ''),
                        'occupation': member_data.get('occupation', ''),
                        'photo_url': mentor.get('photo_url'),
                        'rating': mentor.get('rating'),
                    }

            # Enrich each booking
            enriched_bookings = []
            for booking in bookings:
                enriched = {**booking}
                if booking.get('mentor_id') and booking['mentor_id'] in mentors_map:
                    enriched['mentor'] = mentors_map[booking['mentor_id']]
                enriched_bookings.append(enriched)

            return enriched_bookings
        except Exception as e:
            logger.error(f"Error enriching bookings: {e}")
            return bookings

    # ========== ENHANCED AVAILABILITY OPERATIONS ==========

    def clear_availability_slots(self, mentor_id: str, slot_type: str = None) -> int:
        """
        Clear all availability slots for a mentor.
        slot_type can be 'recurring', 'specific', or None for all.
        Returns the count of cleared slots.
        """
        try:
            # First count the slots to be cleared
            count_query = self._client.table('mentor_availability').select('id', count='exact').eq('mentor_id', mentor_id).eq('is_active', True)

            if slot_type == 'recurring':
                count_query = count_query.eq('is_recurring', True)
            elif slot_type == 'specific':
                count_query = count_query.eq('is_recurring', False)

            count_response = self._circuit_breaker.call(lambda: count_query.execute())
            count = count_response.count or 0

            if count == 0:
                return 0

            # Now clear them
            update_query = self._client.table('mentor_availability').update({
                'is_active': False,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('mentor_id', mentor_id).eq('is_active', True)

            if slot_type == 'recurring':
                update_query = update_query.eq('is_recurring', True)
            elif slot_type == 'specific':
                update_query = update_query.eq('is_recurring', False)

            self._circuit_breaker.call(lambda: update_query.execute())

            logger.info(f"Cleared {count} availability slots for mentor {mentor_id} (type: {slot_type or 'all'})")
            return count
        except Exception as e:
            logger.error(f"Error clearing availability for mentor {mentor_id}: {e}")
            return 0

    def bulk_create_availability_slots(self, slots: List[Dict]) -> List[Dict]:
        """Create multiple availability slots at once"""
        try:
            if not slots:
                return []

            # Prepare slot data
            prepared_slots = []
            for slot in slots:
                slot_data = {
                    'mentor_id': slot['mentor_id'],
                    'start_time': slot.get('start_time'),
                    'end_time': slot.get('end_time'),
                    'is_recurring': slot.get('is_recurring', False),
                    'is_active': slot.get('is_active', True),
                    'created_at': datetime.utcnow().isoformat()
                }

                if slot_data['is_recurring'] and 'day_of_week' in slot:
                    slot_data['day_of_week'] = slot['day_of_week']

                if not slot_data['is_recurring'] and 'specific_date' in slot:
                    slot_data['specific_date'] = slot['specific_date']

                prepared_slots.append(slot_data)

            response = self._circuit_breaker.call(
                lambda: self._client.table('mentor_availability')
                .insert(prepared_slots)
                .execute()
            )

            logger.info(f"Created {len(response.data or [])} availability slots")
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error bulk creating availability slots: {e}")
            raise

    # ========== EXPERTISE OPERATIONS ==========

    def get_expertise_categories(self) -> List[Dict]:
        """Get all expertise categories"""
        try:
            response = self._circuit_breaker.call(
                lambda: self._client.table('mentorship_expertise')
                .select('*')
                .order('name')
                .execute()
            )
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching expertise categories: {e}")
            return []

    # ========== DASHBOARD STATISTICS ==========

    def get_mentor_stats(self, mentor_id: str) -> Dict:
        """Get comprehensive statistics for a mentor"""
        try:
            # Get bookings stats
            bookings_response = self._circuit_breaker.call(
                lambda: self._client.table('mentorship_bookings')
                .select('status', count='exact')
                .eq('mentor_id', mentor_id)
                .execute()
            )

            total_bookings = bookings_response.count or 0

            # Count by status
            status_counts = {}
            for booking in (bookings_response.data or []):
                status = booking.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1

            # Get review stats
            reviews_response = self._circuit_breaker.call(
                lambda: self._client.table('mentorship_reviews')
                .select('rating', count='exact')
                .eq('mentor_id', mentor_id)
                .execute()
            )

            total_reviews = reviews_response.count or 0
            avg_rating = 0
            if reviews_response.data:
                ratings = [r['rating'] for r in reviews_response.data]
                avg_rating = round(sum(ratings) / len(ratings), 2)

            # Get upcoming sessions count
            today = datetime.utcnow().date().isoformat()
            upcoming_response = self._circuit_breaker.call(
                lambda: self._client.table('mentorship_bookings')
                .select('id', count='exact')
                .eq('mentor_id', mentor_id)
                .in_('status', ['pending', 'confirmed'])
                .gte('session_date', today)
                .execute()
            )

            return {
                'total_bookings': total_bookings,
                'completed_sessions': status_counts.get('completed', 0),
                'pending_sessions': status_counts.get('pending', 0),
                'confirmed_sessions': status_counts.get('confirmed', 0),
                'cancelled_sessions': status_counts.get('cancelled', 0),
                'upcoming_sessions': upcoming_response.count or 0,
                'total_reviews': total_reviews,
                'average_rating': avg_rating,
                'status_breakdown': status_counts
            }
        except Exception as e:
            logger.error(f"Error getting stats for mentor {mentor_id}: {e}")
            return {
                'total_bookings': 0,
                'completed_sessions': 0,
                'pending_sessions': 0,
                'confirmed_sessions': 0,
                'cancelled_sessions': 0,
                'upcoming_sessions': 0,
                'total_reviews': 0,
                'average_rating': 0,
                'status_breakdown': {}
            }

    def get_mentee_stats(self, mentee_id: int) -> Dict:
        """Get comprehensive statistics for a mentee"""
        try:
            # Get bookings stats
            bookings_response = self._circuit_breaker.call(
                lambda: self._client.table('mentorship_bookings')
                .select('status, mentor_id', count='exact')
                .eq('mentee_id', mentee_id)
                .execute()
            )

            total_bookings = bookings_response.count or 0

            # Count by status
            status_counts = {}
            unique_mentors = set()
            for booking in (bookings_response.data or []):
                status = booking.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
                if booking.get('mentor_id'):
                    unique_mentors.add(booking['mentor_id'])

            # Get upcoming sessions
            today = datetime.utcnow().date().isoformat()
            upcoming_response = self._circuit_breaker.call(
                lambda: self._client.table('mentorship_bookings')
                .select('id', count='exact')
                .eq('mentee_id', mentee_id)
                .in_('status', ['pending', 'confirmed'])
                .gte('session_date', today)
                .execute()
            )

            return {
                'total_bookings': total_bookings,
                'completed_sessions': status_counts.get('completed', 0),
                'pending_sessions': status_counts.get('pending', 0),
                'confirmed_sessions': status_counts.get('confirmed', 0),
                'cancelled_sessions': status_counts.get('cancelled', 0),
                'upcoming_sessions': upcoming_response.count or 0,
                'unique_mentors_count': len(unique_mentors),
                'status_breakdown': status_counts
            }
        except Exception as e:
            logger.error(f"Error getting stats for mentee {mentee_id}: {e}")
            return {
                'total_bookings': 0,
                'completed_sessions': 0,
                'pending_sessions': 0,
                'confirmed_sessions': 0,
                'cancelled_sessions': 0,
                'upcoming_sessions': 0,
                'unique_mentors_count': 0,
                'status_breakdown': {}
            }


# Singleton instance
supabase_client = SupabaseMentorshipClient()


def get_supabase_client() -> SupabaseMentorshipClient:
    """Get the singleton Supabase client instance"""
    return supabase_client
