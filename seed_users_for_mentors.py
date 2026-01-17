#!/usr/bin/env python
"""
Script to update existing mentors with enriched user data
This adds fake user objects so the frontend can display mentor names
"""
import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env file")
    sys.exit(1)

# Setup headers for Supabase REST API
headers = {
    'apikey': SUPABASE_SERVICE_KEY,
    'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
}

# Mentor names (matching the user_ids we created)
mentor_names = {
    1001: {"first_name": "Sarah", "last_name": "Johnson", "email": "sarah.johnson@example.com"},
    1002: {"first_name": "Michael", "last_name": "Chen", "email": "michael.chen@example.com"},
    1003: {"first_name": "Amara", "last_name": "Okafor", "email": "amara.okafor@example.com"},
    1004: {"first_name": "Fatima", "last_name": "Al-Hassan", "email": "fatima.alhassan@example.com"},
    1005: {"first_name": "James", "last_name": "Mensah", "email": "james.mensah@example.com"},
    1006: {"first_name": "Priya", "last_name": "Sharma", "email": "priya.sharma@example.com"},
    1007: {"first_name": "David", "last_name": "Osei", "email": "david.osei@example.com"},
    1008: {"first_name": "Lisa", "last_name": "Wang", "email": "lisa.wang@example.com"},
    1009: {"first_name": "Kwame", "last_name": "Boateng", "email": "kwame.boateng@example.com"},
    1010: {"first_name": "Maria", "last_name": "Rodriguez", "email": "maria.rodriguez@example.com"},
}

def create_users_table():
    """Create users_user table if it doesn't exist"""
    print("\n" + "=" * 80)
    print("Creating users_user table in Supabase")
    print("=" * 80 + "\n")
    
    sql_url = f"{SUPABASE_URL}/rest/v1/rpc/exec"
    
    # SQL to create the table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS public.users_user (
        id INTEGER PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        first_name VARCHAR(150),
        last_name VARCHAR(150),
        phone_number VARCHAR(20),
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_users_email ON public.users_user(email);
    """
    
    # Note: Supabase REST API doesn't support direct SQL execution
    # We'll need to do this via SQL editor or create records directly
    print("⚠️  Note: Please run this SQL in your Supabase SQL Editor:")
    print("\n" + create_table_sql)
    print("\n")

def seed_users():
    """Insert test users into Supabase"""
    print("\n" + "=" * 80)
    print("Seeding Test Users into Supabase")
    print("=" * 80 + "\n")
    
    api_url = f"{SUPABASE_URL}/rest/v1/users_user"
    
    success_count = 0
    error_count = 0
    
    for user_id, user_data in mentor_names.items():
        try:
            user_record = {
                "id": user_id,
                "email": user_data["email"],
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
                "phone_number": "+1234567890",
                "is_active": True
            }
            
            # Make POST request to insert user
            response = requests.post(api_url, json=user_record, headers=headers)
            
            if response.status_code in [200, 201]:
                success_count += 1
                print(f"✅ Created user: {user_data['first_name']} {user_data['last_name']} (ID: {user_id})")
            elif response.status_code == 409:
                # Duplicate key error
                error_count += 1
                print(f"⚠️  User ID {user_id} already exists, skipping...")
            else:
                error_count += 1
                print(f"❌ Failed to create user ID {user_id}")
                print(f"   Status: {response.status_code}, Response: {response.text[:200]}")
                
        except Exception as e:
            error_count += 1
            print(f"❌ Error creating user ID {user_id}: {e}")
    
    print("\n" + "=" * 80)
    print(f"User Seeding Complete!")
    print(f"✅ Successfully created: {success_count} users")
    if error_count > 0:
        print(f"⚠️  Skipped/Errors: {error_count} users")
    print("=" * 80 + "\n")

def verify_mentors():
    """Verify mentors can be fetched with user data"""
    print("Verifying mentors with user data...\n")
    
    try:
        # Get all mentors
        mentors_url = f"{SUPABASE_URL}/rest/v1/mentors?is_approved=eq.true&select=*"
        response = requests.get(mentors_url, headers=headers)
        
        if response.status_code == 200:
            mentors = response.json()
            print(f"📊 Total approved mentors: {len(mentors)}\n")
            
            # Check if users exist for each mentor
            for mentor in mentors[:3]:  # Check first 3
                user_id = mentor['user_id']
                user_url = f"{SUPABASE_URL}/rest/v1/users_user?id=eq.{user_id}&select=*"
                user_response = requests.get(user_url, headers=headers)
                
                if user_response.status_code == 200:
                    users = user_response.json()
                    if users:
                        user = users[0]
                        print(f"✅ Mentor (user_id: {user_id}): {user['first_name']} {user['last_name']}")
                    else:
                        print(f"❌ No user found for mentor with user_id: {user_id}")
        else:
            print(f"❌ Error fetching mentors: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error verifying: {e}")

if __name__ == '__main__':
    print("\n🚀 Starting User Data Setup for Mentors\n")
    print("This script will create user records for the test mentors.")
    print("These user records are needed for the frontend to display mentor names.\n")
    
    # First, show SQL for creating the table
    create_users_table()
    
    # Ask user to confirm they've run the SQL
    response = input("Have you run the SQL in Supabase SQL Editor? (y/n): ")
    
    if response.lower() == 'y':
        # Seed the users
        seed_users()
        
        # Verify
        verify_mentors()
    else:
        print("\n⚠️  Please run the SQL in Supabase SQL Editor first, then run this script again.")
