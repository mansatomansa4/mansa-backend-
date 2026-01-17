#!/usr/bin/env python
"""
Script to seed test mentors in Supabase database using HTTP requests
This creates approved mentors that will be visible on the platform
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
    print(f"Current SUPABASE_URL: {SUPABASE_URL or 'Not set'}")
    sys.exit(1)

# Sample mentor data
test_mentors = [
    {
        "user_id": 1001,
        "bio": "Senior Software Engineer with 10+ years of experience in full-stack development. Specialized in React, Node.js, and cloud architecture. Passionate about helping aspiring developers break into tech.",
        "expertise": ["Web Development", "Software Engineering", "Career Development", "Technical Interview Prep"],
        "availability_timezone": "UTC",
        "rating": 4.8,
        "total_sessions": 45,
        "is_approved": True,
        "photo_url": "https://ui-avatars.com/api/?name=Sarah+Johnson&size=200&background=random"
    },
    {
        "user_id": 1002,
        "bio": "Product Manager at a leading fintech company. Expert in product strategy, user research, and agile methodologies. Love mentoring PMs and aspiring product leaders.",
        "expertise": ["Product Management", "Business Strategy", "Agile", "User Research"],
        "availability_timezone": "UTC",
        "rating": 4.9,
        "total_sessions": 62,
        "is_approved": True,
        "photo_url": "https://ui-avatars.com/api/?name=Michael+Chen&size=200&background=random"
    },
    {
        "user_id": 1003,
        "bio": "Data Scientist with expertise in machine learning and AI. PhD in Computer Science. Currently working on cutting-edge ML projects and happy to guide others in the field.",
        "expertise": ["Data Science", "Machine Learning", "Python", "AI"],
        "availability_timezone": "UTC",
        "rating": 4.7,
        "total_sessions": 38,
        "is_approved": True,
        "photo_url": "https://ui-avatars.com/api/?name=Amara+Okafor&size=200&background=random"
    },
    {
        "user_id": 1004,
        "bio": "UX/UI Designer with 8 years experience creating beautiful and functional digital experiences. Specialized in design systems, user research, and accessibility.",
        "expertise": ["UI/UX Design", "Design Systems", "User Research", "Figma"],
        "availability_timezone": "UTC",
        "rating": 4.9,
        "total_sessions": 51,
        "is_approved": True,
        "photo_url": "https://ui-avatars.com/api/?name=Fatima+Al-Hassan&size=200&background=random"
    },
    {
        "user_id": 1005,
        "bio": "DevOps Engineer focused on cloud infrastructure, CI/CD, and automation. AWS certified with experience in Kubernetes, Docker, and infrastructure as code.",
        "expertise": ["DevOps", "Cloud Computing", "AWS", "Kubernetes"],
        "availability_timezone": "UTC",
        "rating": 4.6,
        "total_sessions": 29,
        "is_approved": True,
        "photo_url": "https://ui-avatars.com/api/?name=James+Mensah&size=200&background=random"
    },
    {
        "user_id": 1006,
        "bio": "Mobile App Developer specializing in iOS and React Native. Published 15+ apps with millions of downloads. Passionate about mobile UX and performance optimization.",
        "expertise": ["Mobile Development", "iOS", "React Native", "App Design"],
        "availability_timezone": "UTC",
        "rating": 4.8,
        "total_sessions": 42,
        "is_approved": True,
        "photo_url": "https://ui-avatars.com/api/?name=Priya+Sharma&size=200&background=random"
    },
    {
        "user_id": 1007,
        "bio": "Cybersecurity Specialist with focus on application security and ethical hacking. CISSP certified. Help organizations and individuals understand security best practices.",
        "expertise": ["Cybersecurity", "Ethical Hacking", "Security Architecture", "Compliance"],
        "availability_timezone": "UTC",
        "rating": 4.7,
        "total_sessions": 33,
        "is_approved": True,
        "photo_url": "https://ui-avatars.com/api/?name=David+Osei&size=200&background=random"
    },
    {
        "user_id": 1008,
        "bio": "Marketing Director with expertise in digital marketing, growth hacking, and brand strategy. Helped multiple startups achieve exponential growth.",
        "expertise": ["Digital Marketing", "Growth Strategy", "Content Marketing", "SEO"],
        "availability_timezone": "UTC",
        "rating": 4.9,
        "total_sessions": 58,
        "is_approved": True,
        "photo_url": "https://ui-avatars.com/api/?name=Lisa+Wang&size=200&background=random"
    },
    {
        "user_id": 1009,
        "bio": "Finance professional with background in investment banking and startup finance. MBA from top business school. Mentor entrepreneurs on fundraising and financial strategy.",
        "expertise": ["Finance", "Fundraising", "Investment", "Business Development"],
        "availability_timezone": "UTC",
        "rating": 4.8,
        "total_sessions": 47,
        "is_approved": True,
        "photo_url": "https://ui-avatars.com/api/?name=Kwame+Boateng&size=200&background=random"
    },
    {
        "user_id": 1010,
        "bio": "Human Resources leader specializing in talent acquisition, organizational development, and diversity & inclusion. 12+ years experience in tech companies.",
        "expertise": ["Human Resources", "Talent Acquisition", "Career Coaching", "Leadership"],
        "availability_timezone": "UTC",
        "rating": 4.9,
        "total_sessions": 65,
        "is_approved": True,
        "photo_url": "https://ui-avatars.com/api/?name=Maria+Rodriguez&size=200&background=random"
    }
]

def seed_mentors():
    """Insert test mentors into Supabase using REST API"""
    print("\n" + "=" * 80)
    print("Seeding Test Mentors into Supabase")
    print("=" * 80 + "\n")
    
    # Setup headers for Supabase REST API
    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    
    api_url = f"{SUPABASE_URL}/rest/v1/mentors"
    
    success_count = 0
    error_count = 0
    
    for mentor in test_mentors:
        try:
            # Make POST request to insert mentor
            response = requests.post(api_url, json=mentor, headers=headers)
            
            if response.status_code in [200, 201]:
                success_count += 1
                print(f"✅ Created mentor with user_id {mentor['user_id']}")
            elif response.status_code == 409:
                # Duplicate key error
                error_count += 1
                print(f"⚠️  Mentor with user_id {mentor['user_id']} already exists, skipping...")
            else:
                error_count += 1
                print(f"❌ Failed to create mentor with user_id {mentor['user_id']}")
                print(f"   Status: {response.status_code}, Response: {response.text[:200]}")
                
        except Exception as e:
            error_count += 1
            print(f"❌ Error creating mentor with user_id {mentor['user_id']}: {e}")
    
    print("\n" + "=" * 80)
    print(f"Seeding Complete!")
    print(f"✅ Successfully created: {success_count} mentors")
    if error_count > 0:
        print(f"⚠️  Skipped/Errors: {error_count} mentors")
    print("=" * 80 + "\n")
    
    # Verify the mentors in database
    print("Verifying mentors in database...\n")
    try:
        verify_url = f"{api_url}?is_approved=eq.true&select=*"
        response = requests.get(verify_url, headers=headers)
        
        if response.status_code == 200:
            approved_mentors = response.json()
            
            print(f"📊 Total approved mentors in database: {len(approved_mentors)}")
            
            if approved_mentors:
                print("\nApproved Mentors:")
                for mentor in approved_mentors[:5]:  # Show first 5
                    expertise_list = mentor.get('expertise', [])
                    print(f"  • User ID {mentor['user_id']}: {', '.join(expertise_list[:2])}")
                
                if len(approved_mentors) > 5:
                    print(f"  ... and {len(approved_mentors) - 5} more")
        else:
            print(f"❌ Error verifying mentors: {response.status_code} - {response.text}")
        
    except Exception as e:
        print(f"❌ Error verifying mentors: {e}")

if __name__ == '__main__':
    seed_mentors()
