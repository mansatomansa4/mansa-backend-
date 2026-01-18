-- ============================================================================
-- PHASE A: MERGE MEMBERS TABLES
-- Created: 2026-01-18
-- Purpose: Merge members + community_members into single unified table
-- Dependencies: Task 1.1, 1.2, 1.3 (backups and analysis completed)
-- ============================================================================

-- IMPORTANT: This script performs the following operations:
-- 1. Creates unified members_new table with all fields from both tables
-- 2. Migrates data from members table
-- 3. Migrates additional fields from community_members table
-- 4. Updates FK constraints on dependent tables
-- 5. Performs atomic table rename

-- ============================================================================
-- STEP 1: Create unified members_new table with all fields from both tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.members_new (
    -- Primary Key
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Core fields (from members table)
    name text,
    email text UNIQUE NOT NULL,
    phone text,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    is_active boolean DEFAULT true,
    
    -- Members table specific fields
    country text,
    city text,
    linkedin text,
    experience text,
    areaofexpertise text,
    school text,
    level text,
    occupation text,
    jobtitle text,
    industry text,
    major text,
    gender text,
    membershiptype text,
    skills text,
    
    -- Community_members table specific fields
    joined_date timestamptz,
    profile_picture text,
    bio text,
    location text,
    motivation text
);

-- Add comments for documentation
COMMENT ON TABLE public.members_new IS 'Unified members table combining members and community_members data';
COMMENT ON COLUMN public.members_new.areaofexpertise IS 'Professional area of expertise';
COMMENT ON COLUMN public.members_new.membershiptype IS 'Type of membership';
COMMENT ON COLUMN public.members_new.motivation IS 'Member motivation for joining';

-- Create indexes for common queries
CREATE INDEX idx_members_new_email ON public.members_new(email);
CREATE INDEX idx_members_new_is_active ON public.members_new(is_active);
CREATE INDEX idx_members_new_country ON public.members_new(country);
CREATE INDEX idx_members_new_membershiptype ON public.members_new(membershiptype);
CREATE INDEX idx_members_new_created_at ON public.members_new(created_at);
CREATE INDEX idx_members_new_name ON public.members_new(name);

-- ============================================================================
-- STEP 2: Migrate data from members table
-- ============================================================================

INSERT INTO public.members_new (
    id, name, email, phone, created_at, updated_at, is_active,
    country, city, linkedin, experience, areaofexpertise, school, level,
    occupation, jobtitle, industry, major, gender, membershiptype, skills
)
SELECT 
    id, name, email, phone, created_at, updated_at, is_active,
    country, city, linkedin, experience, "areaOfExpertise", school, level,
    occupation, jobtitle, industry, major, gender, membershiptype, skills
FROM public.members;

-- Verify migration
SELECT 
    'Step 2: Migrated from members' AS step,
    (SELECT COUNT(*) FROM public.members) AS source_count,
    (SELECT COUNT(*) FROM public.members_new) AS target_count,
    CASE 
        WHEN (SELECT COUNT(*) FROM public.members) = (SELECT COUNT(*) FROM public.members_new)
        THEN '✅ MATCH'
        ELSE '❌ MISMATCH'
    END AS status;

-- ============================================================================
-- STEP 3: Update with extended fields from community_members
-- ============================================================================

-- Note: This updates existing records with community_members data
-- The community_members.id is a FK to members.id, so it's a 1:1 or 1:0 relationship
-- Priority: community_members fields override members fields where they exist

UPDATE public.members_new mn
SET 
    joined_date = COALESCE(cm.joined_date, mn.created_at),
    profile_picture = cm.profile_picture,
    bio = cm.bio,
    location = COALESCE(cm.location, mn.city),
    motivation = cm.motivation,
    -- If community_members has different values, use them (they're more recent)
    name = COALESCE(cm.name, mn.name),
    phone = COALESCE(cm.phone, mn.phone),
    skills = COALESCE(cm.skills, mn.skills),
    updated_at = GREATEST(COALESCE(cm.updated_at, mn.updated_at), COALESCE(mn.updated_at, cm.updated_at))
FROM public.community_members cm
WHERE mn.id = cm.id;

-- Verify update
SELECT 
    'Step 3: Updated with community_members data' AS step,
    (SELECT COUNT(*) FROM public.community_members) AS community_members_count,
    (SELECT COUNT(*) FROM public.members_new WHERE profile_picture IS NOT NULL OR bio IS NOT NULL) AS members_with_community_data,
    CASE 
        WHEN (SELECT COUNT(*) FROM public.community_members) <= (SELECT COUNT(*) FROM public.members_new WHERE profile_picture IS NOT NULL OR bio IS NOT NULL OR motivation IS NOT NULL)
        THEN '✅ COMMUNITY DATA MERGED'
        ELSE '⚠️ CHECK MERGE RESULTS'
    END AS status;
-- ============================================================================
-- STEP 4: Show summary statistics before FK updates
-- ============================================================================

SELECT 
    'Summary Statistics' AS report_type,
    (SELECT COUNT(*) FROM public.members_new) AS total_members,
    (SELECT COUNT(*) FROM public.members_new WHERE country IS NOT NULL) AS members_with_location,
    (SELECT COUNT(*) FROM public.members_new WHERE areaofexpertise IS NOT NULL) AS members_with_expertise,
    (SELECT COUNT(*) FROM public.members_new WHERE profile_picture IS NOT NULL) AS members_with_photos,
    (SELECT COUNT(*) FROM public.members_new WHERE bio IS NOT NULL) AS members_with_bio,
    (SELECT COUNT(*) FROM public.members_new WHERE linkedin IS NOT NULL) AS members_with_linkedin;

-- ============================================================================
-- NEXT STEPS (Run in separate script after verification):
-- ============================================================================

-- After verifying the above results are correct, run the FK update script:
-- 1. Update FK constraints on dependent tables (003_phase_a_update_foreign_keys.sql)
-- 2. Atomic table rename (004_phase_a_atomic_rename.sql)
-- 3. Drop old tables (005_phase_a_cleanup.sql)

-- DO NOT proceed until stakeholder verifies:
-- ✅ All 131 members migrated successfully
-- ✅ Community_members data properly merged
-- ✅ Summary statistics look correct
