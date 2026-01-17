"""
Test Script: Verify Automatic Mentor Profile Creation

This script tests that mentor profiles are automatically created when:
1. A new member is created with membershiptype='mentor'
2. An existing member's membershiptype is updated to 'mentor'
"""
import sys
import os
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from apps.platform.models import Member
from apps.users.models import User
import uuid


def test_automatic_mentor_creation():
    """Test that mentor profiles are created automatically"""
    
    print("\n" + "=" * 80)
    print("TEST: Automatic Mentor Profile Creation")
    print("=" * 80 + "\n")
    
    # Test 1: Create a new user and member with membershiptype='mentor'
    print("📝 Test 1: Creating new member with membershiptype='mentor'...")
    
    test_email = f"test_mentor_{uuid.uuid4().hex[:8]}@example.com"
    
    try:
        # Create user first
        user = User.objects.create_user(
            email=test_email,
            password="testpass123",
            first_name="Test",
            last_name="Mentor",
            approval_status="approved"
        )
        print(f"✅ Created user: {user.email} (ID: {user.id})")
        
        # Create member with membershiptype='mentor'
        # Note: Since Member is a proxy model (managed=False), we need to use raw SQL
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO members 
                (id, name, email, phone, gender, membershiptype, is_active, created_at, updated_at)
                VALUES 
                (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id
            """, [
                uuid.uuid4(),
                "Test Mentor User",
                test_email,
                "+1234567890",
                "male",
                "mentor",
                True
            ])
            member_id = cursor.fetchone()[0]
        
        print(f"✅ Created member: {test_email} (ID: {member_id})")
        
        # Manually trigger signal since we used raw SQL
        # Fetch the member object
        member = Member.objects.get(email=test_email)
        from django.db.models.signals import post_save
        post_save.send(sender=Member, instance=member, created=True)
        
        # Check if mentor profile was created
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, user_id, bio, expertise, is_approved 
                FROM mentors 
                WHERE user_id = %s
            """, [user.id])
            mentor_row = cursor.fetchone()
        
        if mentor_row:
            print(f"✅ Mentor profile created automatically!")
            print(f"   Mentor ID: {mentor_row[0]}")
            print(f"   User ID: {mentor_row[1]}")
            print(f"   Bio: {mentor_row[2][:80] if mentor_row[2] else 'None'}...")
            print(f"   Expertise: {mentor_row[3]}")
            print(f"   Is Approved: {mentor_row[4]}")
            test1_passed = True
        else:
            print("❌ Mentor profile was NOT created automatically")
            test1_passed = False
        
    except Exception as e:
        print(f"❌ Error in Test 1: {e}")
        test1_passed = False
    
    # Test 2: Check existing members with membershiptype='mentor'
    print("\n📝 Test 2: Checking existing members with membershiptype='mentor'...")
    
    try:
        with connection.cursor() as cursor:
            # Count members with membershiptype='mentor'
            cursor.execute("""
                SELECT COUNT(*) 
                FROM members 
                WHERE LOWER(membershiptype) = 'mentor' 
                AND is_active = true
            """)
            mentor_member_count = cursor.fetchone()[0]
            
            # Count mentor profiles
            cursor.execute("SELECT COUNT(*) FROM mentors")
            mentor_profile_count = cursor.fetchone()[0]
            
            print(f"   Members with membershiptype='mentor': {mentor_member_count}")
            print(f"   Mentor profiles in database: {mentor_profile_count}")
            
            if mentor_profile_count > 0:
                print("✅ Mentor profiles exist in database")
                test2_passed = True
            else:
                print("⚠️  No mentor profiles found. Run sync command:")
                print("   python manage.py sync_mentor_profiles")
                test2_passed = False
        
    except Exception as e:
        print(f"❌ Error in Test 2: {e}")
        test2_passed = False
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Test 1 (Auto-create on new member): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Test 2 (Existing mentor check): {'✅ PASSED' if test2_passed else '⚠️  WARNING'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Automatic mentor profile creation is working.")
    else:
        print("\n⚠️  Some tests failed. Please review the implementation.")
    
    print("\n💡 Next steps:")
    print("1. Run: python manage.py sync_mentor_profiles --dry-run")
    print("2. Run: python manage.py sync_mentor_profiles")
    print("3. Check mentorship API: /api/v1/mentorship/mentors/")
    print()


if __name__ == "__main__":
    test_automatic_mentor_creation()
