#!/usr/bin/env python
"""
Execute the SQL script to create users_user table and seed data
"""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    sys.exit(1)

headers = {
    'apikey': SUPABASE_SERVICE_KEY,
    'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
    'Content-Type': 'application/json'
}

# SQL to create table
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
CREATE INDEX IF NOT EXISTS idx_users_user_email ON public.users_user(email);
"""

# Users data
users_data = [
    {"id": 1001, "email": "sarah.johnson@example.com", "first_name": "Sarah", "last_name": "Johnson", "phone_number": "+1234567890", "is_active": True},
    {"id": 1002, "email": "michael.chen@example.com", "first_name": "Michael", "last_name": "Chen", "phone_number": "+1234567891", "is_active": True},
    {"id": 1003, "email": "amara.okafor@example.com", "first_name": "Amara", "last_name": "Okafor", "phone_number": "+1234567892", "is_active": True},
    {"id": 1004, "email": "fatima.alhassan@example.com", "first_name": "Fatima", "last_name": "Al-Hassan", "phone_number": "+1234567893", "is_active": True},
    {"id": 1005, "email": "james.mensah@example.com", "first_name": "James", "last_name": "Mensah", "phone_number": "+1234567894", "is_active": True},
    {"id": 1006, "email": "priya.sharma@example.com", "first_name": "Priya", "last_name": "Sharma", "phone_number": "+1234567895", "is_active": True},
    {"id": 1007, "email": "david.osei@example.com", "first_name": "David", "last_name": "Osei", "phone_number": "+1234567896", "is_active": True},
    {"id": 1008, "email": "lisa.wang@example.com", "first_name": "Lisa", "last_name": "Wang", "phone_number": "+1234567897", "is_active": True},
    {"id": 1009, "email": "kwame.boateng@example.com", "first_name": "Kwame", "last_name": "Boateng", "phone_number": "+1234567898", "is_active": True},
    {"id": 1010, "email": "maria.rodriguez@example.com", "first_name": "Maria", "last_name": "Rodriguez", "phone_number": "+1234567899", "is_active": True},
]

print("\n" + "=" * 80)
print("Creating users_user table and seeding data")
print("=" * 80 + "\n")

print("📝 Note: Table creation must be done via Supabase SQL Editor")
print("Copy this SQL and run it in Supabase Dashboard:\n")
print(create_table_sql)
print("\n" + "=" * 80 + "\n")

input("Press Enter after you've run the SQL in Supabase, or Ctrl+C to exit...")

# Now insert users via REST API
api_url = f"{SUPABASE_URL}/rest/v1/users_user"

success = 0
errors = 0

for user in users_data:
    try:
        # Use upsert to handle conflicts
        response = requests.post(
            api_url,
            json=user,
            headers={**headers, 'Prefer': 'resolution=merge-duplicates'}
        )
        
        if response.status_code in [200, 201]:
            success += 1
            print(f"✅ Created/Updated: {user['first_name']} {user['last_name']}")
        elif response.status_code == 409:
            print(f"⚠️  Already exists: {user['first_name']} {user['last_name']}")
            errors += 1
        else:
            print(f"❌ Failed: {user['first_name']} {user['last_name']} - {response.status_code}")
            errors += 1
    except Exception as e:
        print(f"❌ Error: {user['first_name']} {user['last_name']} - {e}")
        errors += 1

print("\n" + "=" * 80)
print(f"✅ Successfully created/updated: {success} users")
if errors > 0:
    print(f"⚠️  Errors/Duplicates: {errors}")
print("=" * 80 + "\n")

# Verify
print("Verifying data...\n")
try:
    response = requests.get(f"{api_url}?select=*&order=id", headers=headers)
    if response.status_code == 200:
        users = response.json()
        print(f"📊 Total users in database: {len(users)}\n")
        for user in users:
            print(f"  {user['id']}: {user['first_name']} {user['last_name']} ({user['email']})")
    else:
        print(f"❌ Failed to verify: {response.status_code}")
except Exception as e:
    print(f"❌ Error verifying: {e}")
