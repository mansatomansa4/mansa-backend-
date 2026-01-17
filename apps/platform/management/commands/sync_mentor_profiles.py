"""
Django Management Command: Sync Mentor Profiles from Members Table

This command creates mentor profiles for all members in the database 
who have membershiptype='mentor' but don't have a mentor profile yet.
"""
import logging
from django.core.management.base import BaseCommand
from django.db import connection
from apps.platform.models import Member
from apps.users.models import User

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create mentor profiles for all members with membershiptype="mentor"'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating anything',
        )
        parser.add_argument(
            '--auto-approve',
            action='store_true',
            default=True,
            help='Auto-approve mentor profiles (default: True)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        auto_approve = options['auto_approve']
        
        self.stdout.write(self.style.WARNING('=' * 80))
        self.stdout.write(self.style.WARNING('Sync Mentor Profiles from Members Table'))
        self.stdout.write(self.style.WARNING('=' * 80))
        
        if dry_run:
            self.stdout.write(self.style.NOTICE('🔍 DRY RUN MODE - No changes will be made\n'))
        
        # Find all members with membershiptype='mentor'
        mentor_members = Member.objects.filter(membershiptype__iexact='mentor', is_active=True)
        total_members = mentor_members.count()
        
        self.stdout.write(f"Found {total_members} active members with membershiptype='mentor'\n")
        
        if total_members == 0:
            self.stdout.write(self.style.SUCCESS('✅ No mentor members found. Nothing to do.'))
            return
        
        created_count = 0
        skipped_count = 0
        error_count = 0
        no_user_count = 0
        
        for member in mentor_members:
            try:
                with connection.cursor() as cursor:
                    # Check if user exists for this member's email
                    cursor.execute("""
                        SELECT id, email, first_name, last_name 
                        FROM users_user 
                        WHERE email = %s 
                        LIMIT 1
                    """, [member.email])
                    
                    user_row = cursor.fetchone()
                    
                    if not user_row:
                        no_user_count += 1
                        self.stdout.write(
                            self.style.NOTICE(
                                f"⏭️  Skipped: {member.name} ({member.email}) - No user account found"
                            )
                        )
                        continue
                    
                    user_id = user_row[0]
                    
                    # Check if mentor profile already exists
                    cursor.execute("""
                        SELECT id FROM mentors 
                        WHERE user_id = %s 
                        LIMIT 1
                    """, [user_id])
                    
                    existing_mentor = cursor.fetchone()
                    
                    if existing_mentor:
                        skipped_count += 1
                        self.stdout.write(
                            self.style.NOTICE(
                                f"⏭️  Skipped: {member.name} ({member.email}) - Mentor profile already exists"
                            )
                        )
                        continue
                    
                    # Prepare data for mentor profile
                    expertise = []
                    if member.areaOfExpertise:
                        expertise.append(member.areaOfExpertise)
                    if member.industry:
                        expertise.append(member.industry)
                    if member.skills:
                        # Split skills if comma-separated
                        skills_list = [s.strip() for s in member.skills.split(',') if s.strip()]
                        expertise.extend(skills_list[:3])  # Add up to 3 skills
                    
                    # Remove duplicates
                    expertise = list(set(expertise))
                    
                    # Prepare bio
                    bio_parts = []
                    if member.experience:
                        bio_parts.append(f"Experience: {member.experience}")
                    if member.occupation:
                        bio_parts.append(f"Occupation: {member.occupation}")
                    if member.jobtitle:
                        bio_parts.append(f"Job Title: {member.jobtitle}")
                    if member.school:
                        bio_parts.append(f"Education: {member.school}")
                    
                    bio = " | ".join(bio_parts) if bio_parts else "Experienced mentor ready to help you grow."
                    
                    if dry_run:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✅ Would create mentor profile for: {member.name} ({member.email})"
                            )
                        )
                        self.stdout.write(f"   User ID: {user_id}")
                        self.stdout.write(f"   Expertise: {expertise}")
                        self.stdout.write(f"   Bio: {bio[:80]}...")
                        created_count += 1
                    else:
                        # Create mentor profile
                        cursor.execute("""
                            INSERT INTO mentors 
                            (user_id, bio, expertise, is_approved, rating, total_sessions, version, created_at, updated_at)
                            VALUES 
                            (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                            RETURNING id
                        """, [
                            user_id,
                            bio,
                            expertise,
                            auto_approve,
                            0.00,
                            0,
                            1
                        ])
                        
                        mentor_id = cursor.fetchone()[0]
                        created_count += 1
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✅ Created mentor profile (ID: {mentor_id}) for: {member.name} ({member.email})"
                            )
                        )
                        
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Error processing {member.name} ({member.email}): {e}"
                    )
                )
                logger.error(f"Error creating mentor profile for {member.email}: {e}", exc_info=True)
        
        # Summary
        self.stdout.write(self.style.WARNING('\n' + '=' * 80))
        self.stdout.write(self.style.WARNING('SUMMARY'))
        self.stdout.write(self.style.WARNING('=' * 80))
        self.stdout.write(f"Total mentor members found: {total_members}")
        self.stdout.write(self.style.SUCCESS(f"✅ Mentor profiles created: {created_count}"))
        self.stdout.write(self.style.NOTICE(f"⏭️  Skipped (already exist): {skipped_count}"))
        self.stdout.write(self.style.NOTICE(f"⏭️  Skipped (no user account): {no_user_count}"))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"❌ Errors: {error_count}"))
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\n💡 This was a dry run. Run without --dry-run to actually create mentor profiles.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    '\n🎉 Sync completed successfully!'
                )
            )
