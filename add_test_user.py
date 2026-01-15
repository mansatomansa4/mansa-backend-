#!/usr/bin/env python
"""
Quick script to add a test user to the database for mentorship testing.
Run: python add_test_user.py
"""

import os
import sys
import django

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from apps.users.models import User

def add_test_user(email, first_name='Test', last_name='User', is_mentee=True, is_mentor=False):
    """Add or update a test user."""
    email = email.strip().lower()
    
    try:
        user = User.objects.get(email=email)
        print(f"✓ User already exists: {email}")
        print(f"  ID: {user.id}")
        print(f"  Name: {user.first_name} {user.last_name}")
        print(f"  Is Mentor: {user.is_mentor}")
        print(f"  Is Mentee: {user.is_mentee}")
        print(f"  Approval Status: {user.approval_status}")
        
        # Update if needed
        updated = False
        if user.approval_status != 'approved':
            user.approval_status = 'approved'
            updated = True
        if is_mentee and not user.is_mentee:
            user.is_mentee = True
            updated = True
        if is_mentor and not user.is_mentor:
            user.is_mentor = True
            updated = True
            
        if updated:
            user.save()
            print("\n✓ User updated successfully!")
            
        return user
        
    except User.DoesNotExist:
        print(f"Creating new user: {email}")
        user = User.objects.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_mentee=is_mentee,
            is_mentor=is_mentor,
            approval_status='approved',
        )
        print(f"\n✓ User created successfully!")
        print(f"  ID: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Name: {user.first_name} {user.last_name}")
        return user

if __name__ == '__main__':
    # Add the test user
    email = 'wuniabdulai199@gmail.com'
    
    print(f"\n{'='*60}")
    print(f"Adding/Checking User: {email}")
    print(f"{'='*60}\n")
    
    user = add_test_user(
        email=email,
        first_name='Wuni',
        last_name='Abdulai',
        is_mentee=True,
        is_mentor=False
    )
    
    print(f"\n{'='*60}")
    print("Done! User can now login at:")
    print("https://www.mansa-to-mansa.org/community/mentorship/auth")
    print(f"{'='*60}\n")
