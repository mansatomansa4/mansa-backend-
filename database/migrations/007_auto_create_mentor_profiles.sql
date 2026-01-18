-- =====================================================
-- AUTO-CREATE MENTOR PROFILES FROM MEMBERS
-- =====================================================
-- When a member has membershiptype='mentor', automatically
-- create a corresponding mentor profile
-- =====================================================

-- Step 1: First, let's see if we need to modify mentors table structure
-- Check if mentors table has member_id column

-- Add member_id to mentors table if it doesn't exist
ALTER TABLE mentors 
ADD COLUMN IF NOT EXISTS member_id uuid REFERENCES members(id) ON DELETE CASCADE;

-- Drop the unique constraint on user_id if it exists (causes conflicts with placeholder values)
ALTER TABLE mentors 
DROP CONSTRAINT IF EXISTS mentors_user_id_key;

-- Make user_id nullable since member_id is now the primary reference
ALTER TABLE mentors 
ALTER COLUMN user_id DROP NOT NULL;

-- Add unique constraint to prevent duplicate mentor profiles per member
ALTER TABLE mentors
ADD CONSTRAINT mentors_member_id_unique UNIQUE (member_id);

-- Step 2: Create function to auto-create mentor profile
CREATE OR REPLACE FUNCTION auto_create_mentor_profile()
RETURNS TRIGGER AS $$
BEGIN
    -- Only proceed if membershiptype is 'mentor' or 'Mentor'
    IF (NEW.membershiptype ILIKE 'mentor') THEN
        -- Check if mentor profile already exists for this member
        IF NOT EXISTS (SELECT 1 FROM mentors WHERE member_id = NEW.id) THEN
            -- Create mentor profile with member data
            INSERT INTO mentors (
                member_id,
                user_id,
                bio,
                photo_url,
                expertise,
                availability_timezone,
                is_approved,
                created_at,
                updated_at
            ) VALUES (
                NEW.id,
                NULL, -- user_id is now nullable, member_id is the primary reference
                NEW.bio,
                NEW.profile_picture,
                COALESCE(
                    CASE 
                        WHEN NEW.areaofexpertise IS NOT NULL 
                        THEN jsonb_build_array(NEW.areaofexpertise)
                        ELSE '[]'::jsonb
                    END,
                    '[]'::jsonb
                ),
                'UTC',
                true, -- Auto-approve mentors
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            );
        ELSE
            -- Update existing mentor profile with latest member data
            UPDATE mentors
            SET 
                bio = COALESCE(NEW.bio, bio),
                photo_url = COALESCE(NEW.profile_picture, photo_url),
                expertise = COALESCE(
                    CASE 
                        WHEN NEW.areaofexpertise IS NOT NULL 
                        THEN jsonb_build_array(NEW.areaofexpertise)
                        ELSE expertise
                    END,
                    expertise
                ),
                updated_at = CURRENT_TIMESTAMP
            WHERE member_id = NEW.id;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 3: Create trigger on members table
DROP TRIGGER IF EXISTS trigger_auto_create_mentor ON members;

CREATE TRIGGER trigger_auto_create_mentor
    AFTER INSERT OR UPDATE OF membershiptype, bio, profile_picture, areaofexpertise
    ON members
    FOR EACH ROW
    EXECUTE FUNCTION auto_create_mentor_profile();

-- Step 4: Backfill existing mentors
-- Create mentor profiles for existing members with membershiptype='mentor'
INSERT INTO mentors (
    member_id,
    user_id,
    bio,
    photo_url,
    expertise,
    availability_timezone,
    is_approved,
    created_at,
    updated_at
)
SELECT 
    m.id,
    NULL, -- user_id is now nullable, member_id is the primary reference
    m.bio,
    m.profile_picture,
    COALESCE(
        CASE 
            WHEN m.areaofexpertise IS NOT NULL 
            THEN jsonb_build_array(m.areaofexpertise)
            ELSE '[]'::jsonb
        END,
        '[]'::jsonb
    ),
    'UTC',
    true,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM members m
WHERE m.membershiptype ILIKE 'mentor'
ON CONFLICT (member_id) DO UPDATE SET
    bio = EXCLUDED.bio,
    photo_url = EXCLUDED.photo_url,
    expertise = EXCLUDED.expertise,
    updated_at = CURRENT_TIMESTAMP;

-- Step 5: Verify the setup
SELECT 
    'Total members with mentor type' as description,
    COUNT(*) as count
FROM members 
WHERE membershiptype ILIKE 'mentor'
UNION ALL
SELECT 
    'Total mentor profiles created',
    COUNT(*)
FROM mentors
WHERE member_id IS NOT NULL;

-- Step 6: Show sample of created mentors with member data
SELECT 
    m.id as member_id,
    m.name,
    m.email,
    m.membershiptype,
    m.areaofexpertise,
    mt.id as mentor_id,
    mt.expertise,
    mt.is_approved
FROM members m
INNER JOIN mentors mt ON mt.member_id = m.id
WHERE m.membershiptype ILIKE 'mentor'
LIMIT 5;

-- =====================================================
-- Expected Result:
-- - member_id column added to mentors table
-- - Trigger created for auto-creation
-- - Existing mentors backfilled
-- - All members with membershiptype='mentor' now have mentor profiles
-- =====================================================
