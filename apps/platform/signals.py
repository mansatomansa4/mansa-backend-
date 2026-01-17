"""
Platform App Signals

Django signals for automatic profile creation based on member data.
"""
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import connection
from .models import Member

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Member)
def create_mentor_profile_for_member(sender, instance, created, **kwargs):
    """
    Automatically create a mentor profile when a member has membershiptype='mentor'.
    
    This signal triggers when:
    1. A new member is created with membershiptype='mentor'
    2. An existing member's membershiptype is updated to 'mentor'
    """
    # Only process if membershiptype is mentor
    if not instance.membershiptype or instance.membershiptype.lower() != 'mentor':
        return
    
    try:
        # Check if this member already has a mentor profile
        with connection.cursor() as cursor:
            # First, check if users_user exists for this member's email
            cursor.execute("""
                SELECT id FROM users_user 
                WHERE email = %s 
                LIMIT 1
            """, [instance.email])
            
            user_row = cursor.fetchone()
            
            if not user_row:
                logger.info(f"No user account found for member {instance.email}. Will create mentor profile when user account is created.")
                return
            
            user_id = user_row[0]
            
            # Check if mentor profile already exists
            cursor.execute("""
                SELECT id FROM mentors 
                WHERE user_id = %s 
                LIMIT 1
            """, [user_id])
            
            existing_mentor = cursor.fetchone()
            
            if existing_mentor:
                logger.info(f"Mentor profile already exists for user_id {user_id} (member: {instance.email})")
                return
            
            # Create mentor profile
            logger.info(f"Creating mentor profile for member {instance.name} ({instance.email}), user_id: {user_id}")
            
            # Prepare expertise from member data
            expertise = []
            if instance.areaOfExpertise:
                expertise.append(instance.areaOfExpertise)
            if instance.industry:
                expertise.append(instance.industry)
            
            # Prepare bio from member data
            bio_parts = []
            if instance.experience:
                bio_parts.append(f"Experience: {instance.experience}")
            if instance.occupation:
                bio_parts.append(f"Occupation: {instance.occupation}")
            if instance.jobtitle:
                bio_parts.append(f"Job Title: {instance.jobtitle}")
            
            bio = " | ".join(bio_parts) if bio_parts else None
            
            # Insert mentor profile
            cursor.execute("""
                INSERT INTO mentors 
                (user_id, bio, expertise, is_approved, rating, total_sessions, version, created_at, updated_at)
                VALUES 
                (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id
            """, [
                user_id,
                bio,
                expertise,  # PostgreSQL will convert Python list to jsonb array
                True,  # Auto-approve mentors from members table
                0.00,
                0,
                1
            ])
            
            mentor_id = cursor.fetchone()[0]
            
            logger.info(f"✅ Successfully created mentor profile (ID: {mentor_id}) for member {instance.name} ({instance.email})")
            
    except Exception as e:
        logger.error(f"❌ Error creating mentor profile for member {instance.email}: {e}", exc_info=True)


@receiver(pre_save, sender=Member)
def check_membershiptype_change(sender, instance, **kwargs):
    """
    Track when membershiptype changes to 'mentor' for existing members.
    Sets a flag so post_save can detect the change.
    """
    if instance.pk:  # Only for existing members
        try:
            old_instance = Member.objects.get(pk=instance.pk)
            # Store the old value for comparison in post_save
            instance._old_membershiptype = old_instance.membershiptype
        except Member.DoesNotExist:
            instance._old_membershiptype = None
    else:
        instance._old_membershiptype = None
