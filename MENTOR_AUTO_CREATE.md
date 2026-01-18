# Auto-Create Mentor Profiles Feature

**Date:** January 18, 2026  
**Status:** ✅ Complete

## Overview

Implemented automatic mentor profile creation when a member has `membershiptype = 'mentor'`. This eliminates manual work and ensures all mentors are immediately visible on the frontend.

---

## How It Works

### Database Trigger (Automatic)
When a member's `membershiptype` is set to 'mentor' (or 'Mentor'), a database trigger automatically:
1. Creates a mentor profile in the `mentors` table
2. Links it via `member_id` foreign key
3. Populates mentor fields from member data:
   - `bio` ← member.bio
   - `photo_url` ← member.profile_picture
   - `expertise` ← member.areaofexpertise
4. Auto-approves the mentor (`is_approved = true`)

### On Update
If member data changes (bio, profile picture, expertise), the trigger updates the existing mentor profile.

---

## Changes Made

### 1. Database Migration ✅

**File:** `database/migrations/007_auto_create_mentor_profiles.sql`

**Actions:**
- Added `member_id` column to `mentors` table
- Created `auto_create_mentor_profile()` function
- Created trigger `trigger_auto_create_mentor` on members table
- Backfilled existing mentors

**Execute in Supabase:**
```sql
-- Run the entire 007_auto_create_mentor_profiles.sql file
```

### 2. Backend Updates ✅

#### Models (`apps/mentorship/models.py`)
- Created full `Mentor` model with all fields
- Added `member_id` field linking to members table
- Created `MentorAvailability` model
- Created `MentorshipBooking` model
- Kept legacy `MentorProxy` and `BookingProxy` for compatibility

#### API Client (`apps/mentorship/supabase_client.py`)
- Updated `get_mentors_with_member_data()` to use `member_id` FK
- Uses Supabase foreign key expansion: `.select('*, member:member_id(*)')`
- Returns enriched mentor data with member information at top level

#### Views (`apps/mentorship/views.py`)
- Already uses `get_mentors_with_member_data()` method
- No changes needed - backwards compatible

### 3. Frontend Updates ✅

**File:** `mansa-redesign/src/app/community/mentorship/page.tsx`

**Changes:**
- Updated `Mentor` interface to include member fields
- Added backwards compatibility for both data structures:
  - New: `mentor.name`, `mentor.email` at top level
  - Legacy: `mentor.user.first_name`, `mentor.user.last_name`
- Updated filtering to work with both structures
- Updated mentor card rendering with fallbacks
- Handles `expertise` as array of strings or objects

---

## Data Flow

```
Member Table (membershiptype='mentor')
    ↓ (Database Trigger)
Mentors Table (member_id FK)
    ↓ (Django API)
Backend enriches with member data
    ↓ (REST API)
Frontend displays mentor cards
```

---

## API Response Structure

### New Format (After Migration)
```json
{
  "results": [
    {
      "id": "uuid",
      "member_id": "uuid",
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+1234567890",
      "country": "USA",
      "city": "New York",
      "location": "New York, USA",
      "linkedin": "https://linkedin.com/in/johndoe",
      "areaofexpertise": "Software Engineering",
      "bio": "Experienced software engineer...",
      "photo_url": "https://...",
      "profile_picture": "https://...",
      "expertise": ["Software Engineering"],
      "rating": 4.8,
      "total_sessions": 25,
      "is_approved": true,
      "jobtitle": "Senior Engineer",
      "occupation": "Software Development",
      "member_data": { /* full member object */ }
    }
  ],
  "count": 1,
  "page": 1,
  "page_size": 12
}
```

---

## Testing Steps

### 1. Execute Database Migration
```sql
-- In Supabase SQL Editor
-- Run: database/migrations/007_auto_create_mentor_profiles.sql
```

### 2. Test Auto-Creation
```sql
-- Update an existing member to be a mentor
UPDATE members 
SET membershiptype = 'mentor' 
WHERE email = 'test@example.com';

-- Verify mentor profile was created
SELECT m.name, m.membershiptype, mt.id as mentor_id, mt.member_id
FROM members m
LEFT JOIN mentors mt ON mt.member_id = m.id
WHERE m.email = 'test@example.com';
```

### 3. Test Backend API
```bash
# Test mentors endpoint
curl http://localhost:8000/api/v1/mentorship/mentors/

# Verify response includes member data
```

### 4. Test Frontend
1. Navigate to `/community/mentorship`
2. Verify mentor cards display correctly
3. Check mentor names, bios, expertise tags
4. Verify photos/avatars display
5. Click mentor card to view profile

---

## Migration Checklist

- [ ] **Database**: Run `007_auto_create_mentor_profiles.sql` in Supabase
- [ ] **Backend**: Already updated (commit/push done)
- [ ] **Frontend**: Already updated (commit/push done)
- [ ] **Test**: Verify trigger creates mentors automatically
- [ ] **Test**: Check API returns enriched data
- [ ] **Test**: Confirm frontend displays mentors
- [ ] **Monitor**: Watch for any errors in logs

---

## Troubleshooting

### Mentor not showing in frontend?
1. Check `membershiptype` is exactly 'mentor' or 'Mentor'
2. Verify mentor profile exists: `SELECT * FROM mentors WHERE member_id = '<uuid>'`
3. Check `is_approved = true` in mentors table
4. Verify API response includes the mentor

### API returns empty member data?
1. Check `member_id` is populated in mentors table
2. Verify foreign key exists: `\d mentors` in psql
3. Test Supabase foreign key expansion manually

### Trigger not firing?
1. Check trigger exists: `SELECT * FROM pg_trigger WHERE tgname = 'trigger_auto_create_mentor'`
2. Verify function exists: `SELECT * FROM pg_proc WHERE proname = 'auto_create_mentor_profile'`
3. Re-run migration if needed

---

## Rollback (If Needed)

```sql
-- Drop trigger
DROP TRIGGER IF EXISTS trigger_auto_create_mentor ON members;

-- Drop function
DROP FUNCTION IF EXISTS auto_create_mentor_profile();

-- Remove member_id column (optional - will break existing mentor profiles)
-- ALTER TABLE mentors DROP COLUMN IF EXISTS member_id;
```

---

## Benefits

✅ **Automatic** - No manual mentor profile creation needed  
✅ **Real-time** - Mentors appear instantly when member type changes  
✅ **Synchronized** - Member data updates reflect in mentor profiles  
✅ **Scalable** - Handles bulk updates efficiently  
✅ **Backwards Compatible** - Works with existing frontend/backend code  

---

## Files Changed

**Backend:**
- `database/migrations/007_auto_create_mentor_profiles.sql` (new)
- `apps/mentorship/models.py` (updated)
- `apps/mentorship/supabase_client.py` (updated)
- `MENTOR_AUTO_CREATE.md` (this file)

**Frontend:**
- `src/app/community/mentorship/page.tsx` (updated)

---

**Next:** Execute the database migration and test!
