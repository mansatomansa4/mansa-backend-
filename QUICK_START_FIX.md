# Quick Start Guide: Getting Mentors to Display on the Platform

## Problem
Mentors are not showing up on the platform at `/community/mentorship`.

## Root Cause
The backend successfully created 10 mentors in the database, but they're missing corresponding user records in the `users_user` table. The API tries to join mentor data with user data, and without users, the enriched response is incomplete or empty.

## Solution Steps

### Step 1: Create users_user Table and Seed Data

Run this SQL in your **Supabase SQL Editor**:

```sql
-- Create users_user table if it doesn't exist
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

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_user_email ON public.users_user(email);

-- Insert test users for the mentors we created
INSERT INTO public.users_user (id, email, first_name, last_name, phone_number, is_active) VALUES
(1001, 'sarah.johnson@example.com', 'Sarah', 'Johnson', '+1234567890', TRUE),
(1002, 'michael.chen@example.com', 'Michael', 'Chen', '+1234567891', TRUE),
(1003, 'amara.okafor@example.com', 'Amara', 'Okafor', '+1234567892', TRUE),
(1004, 'fatima.alhassan@example.com', 'Fatima', 'Al-Hassan', '+1234567893', TRUE),
(1005, 'james.mensah@example.com', 'James', 'Mensah', '+1234567894', TRUE),
(1006, 'priya.sharma@example.com', 'Priya', 'Sharma', '+1234567895', TRUE),
(1007, 'david.osei@example.com', 'David', 'Osei', '+1234567896', TRUE),
(1008, 'lisa.wang@example.com', 'Lisa', 'Wang', '+1234567897', TRUE),
(1009, 'kwame.boateng@example.com', 'Kwame', 'Boateng', '+1234567898', TRUE),
(1010, 'maria.rodriguez@example.com', 'Maria', 'Rodriguez', '+1234567899', TRUE)
ON CONFLICT (id) DO UPDATE SET
    first_name = EXCLUDED.first_name,
    last_name = EXCLUDED.last_name,
    email = EXCLUDED.email,
    updated_at = CURRENT_TIMESTAMP;

-- Verify the data
SELECT id, first_name, last_name, email FROM public.users_user ORDER BY id;
```

**Expected Output**: You should see 10 rows with user data.

### Step 2: Verify Mentors in Database

Run this SQL to check the mentors:

```sql
SELECT 
    m.id,
    m.user_id,
    m.bio,
    m.is_approved,
    u.first_name,
    u.last_name,
    u.email
FROM public.mentors m
LEFT JOIN public.users_user u ON m.user_id = u.id
WHERE m.is_approved = TRUE
ORDER BY m.created_at DESC;
```

**Expected Output**: 10 mentors with their user information populated.

### Step 3: Create Supabase Storage Bucket

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Click **Storage** in the left sidebar
4. Click **"New bucket"**
5. Configure:
   - Name: `profile-pictures`
   - Public bucket: ✅ Enabled
   - Click **"Create bucket"**

### Step 4: Restart Your Backend Server

If your backend is running, restart it to clear any caches:

```bash
# If running locally
Ctrl+C  # Stop the server
python manage.py runserver  # Or your run command

# If on Render
# It should auto-deploy, or manually trigger a deploy
```

### Step 5: Clear Frontend Cache and Reload

1. In your browser, open Developer Tools (F12)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"
4. Or just navigate to: http://localhost:3000/community/mentorship

### Step 6: Verify Mentors Are Displaying

You should now see:
- 10 mentor cards on the main page
- Each with a name, photo placeholder, and basic info
- Click any card to see full profile

## Verification Commands

### Check Mentors in Database
```bash
cd mansa-backend
py -c "import requests; print(requests.get('${SUPABASE_URL}/rest/v1/mentors?is_approved=eq.true&select=*', headers={'apikey': '${SUPABASE_SERVICE_KEY}'}).json())"
```

### Check Users in Database
```bash
py -c "import requests; print(requests.get('${SUPABASE_URL}/rest/v1/users_user?select=*', headers={'apikey': '${SUPABASE_SERVICE_KEY}'}).json())"
```

### Test API Endpoint Directly
```bash
# Replace with your actual backend URL
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/v1/mentorship/mentors/?page=1&page_size=12
```

## Expected Results

After completing these steps:

1. ✅ **Mentor List Page** (`/community/mentorship`):
   - Shows 10 mentor cards
   - Each card displays: name, photo, job title, company, rating
   - Filtering by expertise works
   - Search functionality works

2. ✅ **Mentor Detail Page** (`/community/mentorship/{id}`):
   - Shows complete profile
   - Bio, expertise, experience
   - Social links (if configured)
   - Statistics (rating, sessions, years)

3. ✅ **Profile Editing** (`/community/mentorship/profile/edit`):
   - Mentors can update their info
   - Can upload profile photos
   - Changes save successfully

## Troubleshooting

### Still Not Seeing Mentors?

**Check Backend Logs:**
```bash
# Look for this in your backend logs
[INFO] 2026-01-17 XX:XX:XX apps.mentorship.supabase_client Supabase client initialized successfully
[INFO] 2026-01-17 XX:XX:XX httpx HTTP Request: GET https://...supabase.co/rest/v1/mentors?...
```

**Check API Response:**
Look at the browser Network tab (F12 → Network):
- Find the request to `/api/v1/mentorship/mentors/`
- Check the response
- Should see `"count": 10` and `"results": [...]`

**Common Issues:**

1. **Empty results array**
   - Check `is_approved` is `TRUE` in database
   - Run: `UPDATE mentors SET is_approved = TRUE;`

2. **No user data in response**
   - Verify users_user table has data
   - Check user_id values match between tables

3. **API returns 401/403**
   - Check authentication token is valid
   - Verify user is logged in

4. **API returns 500**
   - Check backend logs for Python errors
   - Verify Supabase credentials in `.env`

## Quick Test Script

Save this as `test_mentors.py` and run it:

```python
import requests
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}'
}

# Check mentors
mentors_url = f"{SUPABASE_URL}/rest/v1/mentors?is_approved=eq.true&select=*"
mentors = requests.get(mentors_url, headers=headers).json()
print(f"✅ Found {len(mentors)} approved mentors")

# Check users
users_url = f"{SUPABASE_URL}/rest/v1/users_user?select=*"
users = requests.get(users_url, headers=headers).json()
print(f"✅ Found {len(users)} users")

# Check if they match
mentor_user_ids = {m['user_id'] for m in mentors}
user_ids = {u['id'] for u in users}
matching = mentor_user_ids & user_ids
print(f"✅ {len(matching)} mentors have matching user records")

if len(matching) == len(mentors):
    print("\n🎉 SUCCESS! All mentors have user records. They should display on the platform.")
else:
    missing = mentor_user_ids - user_ids
    print(f"\n⚠️  WARNING: {len(missing)} mentors are missing user records")
    print(f"Missing user_ids: {missing}")
```

Run it:
```bash
cd mansa-backend
py test_mentors.py
```

## Final Checklist

Before testing on the frontend:

- [ ] SQL script executed successfully in Supabase
- [ ] 10 users created in `users_user` table
- [ ] 10 mentors exist in `mentors` table with `is_approved = TRUE`
- [ ] `profile-pictures` storage bucket created
- [ ] Backend server restarted (if running locally)
- [ ] Frontend cache cleared
- [ ] Logged in as a valid user

## Success!

If you see mentors on the page, congratulations! 🎉

You can now:
1. Click on any mentor to see their full profile
2. Log in as a mentor to edit your profile
3. Upload profile pictures
4. Browse and filter mentors by expertise

## Need Help?

Check these files for detailed information:
- `MENTOR_PROFILE_MANAGEMENT.md` - Full user guide
- `SUPABASE_STORAGE_SETUP.md` - Storage setup details
- `IMPLEMENTATION_SUMMARY.md` - Technical implementation details
