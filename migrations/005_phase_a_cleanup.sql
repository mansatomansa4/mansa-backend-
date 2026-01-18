-- ============================================================================
-- PHASE A: CLEANUP - DROP EMPTY DUPLICATE TABLES
-- Created: 2026-01-18
-- Purpose: Drop all empty duplicate tables after successful migration
-- Dependencies: 004_phase_a_atomic_rename.sql (atomic rename completed)
-- ============================================================================

-- IMPORTANT: Only run this after verifying the member table migration was successful
-- This script drops:
-- 1. Empty Django-managed project tables (projects_project, projects_projectapplication)
-- 2. Empty mentorship_bookings partition tables (14 monthly tables)
-- 3. Create new single mentorship_bookings table

-- ============================================================================
-- SAFETY CHECK: Verify tables are actually empty before dropping
-- ============================================================================

SELECT 
    'projects_project' AS table_name,
    (SELECT COUNT(*) FROM public.projects_project) AS row_count,
    CASE 
        WHEN (SELECT COUNT(*) FROM public.projects_project) = 0 THEN '✅ SAFE TO DROP'
        ELSE '❌ HAS DATA - DO NOT DROP'
    END AS safety_check
UNION ALL
SELECT 
    'projects_projectapplication',
    (SELECT COUNT(*) FROM public.projects_projectapplication),
    CASE 
        WHEN (SELECT COUNT(*) FROM public.projects_projectapplication) = 0 THEN '✅ SAFE TO DROP'
        ELSE '❌ HAS DATA - DO NOT DROP'
    END
UNION ALL
SELECT 
    'mentorship_bookings_2026_01',
    (SELECT COUNT(*) FROM public.mentorship_bookings_2026_01),
    CASE 
        WHEN (SELECT COUNT(*) FROM public.mentorship_bookings_2026_01) = 0 THEN '✅ SAFE TO DROP'
        ELSE '❌ HAS DATA - DO NOT DROP'
    END
UNION ALL
SELECT 
    'mentorship_bookings (parent)',
    (SELECT COUNT(*) FROM public.mentorship_bookings),
    CASE 
        WHEN (SELECT COUNT(*) FROM public.mentorship_bookings) = 0 THEN '✅ SAFE TO DROP'
        ELSE '❌ HAS DATA - DO NOT DROP'
    END;

-- STOP HERE if any table shows "HAS DATA"
-- Review the data before proceeding!

-- ============================================================================
-- STEP 1: Drop empty Django project tables
-- ============================================================================

-- Drop Django-managed project tables (empty, replaced by Supabase tables)
DROP TABLE IF EXISTS public.projects_projectapplication CASCADE;
DROP TABLE IF EXISTS public.projects_project CASCADE;

SELECT '✅ Django project tables dropped' AS status;

-- ============================================================================
-- STEP 2: Drop failed mentorship_bookings partition tables
-- ============================================================================

-- These tables were created as partitions but not properly configured
-- All are empty, and all queries use the parent mentorship_bookings table
-- We'll drop them all and create a proper single table

-- Drop all monthly partition tables
DROP TABLE IF EXISTS public.mentorship_bookings_2026_01 CASCADE;
DROP TABLE IF EXISTS public.mentorship_bookings_2026_02 CASCADE;
DROP TABLE IF EXISTS public.mentorship_bookings_2026_03 CASCADE;
DROP TABLE IF EXISTS public.mentorship_bookings_2026_04 CASCADE;
DROP TABLE IF EXISTS public.mentorship_bookings_2026_05 CASCADE;
DROP TABLE IF EXISTS public.mentorship_bookings_2026_06 CASCADE;
DROP TABLE IF EXISTS public.mentorship_bookings_2026_07 CASCADE;
DROP TABLE IF EXISTS public.mentorship_bookings_2026_08 CASCADE;
DROP TABLE IF EXISTS public.mentorship_bookings_2026_09 CASCADE;
DROP TABLE IF EXISTS public.mentorship_bookings_2026_10 CASCADE;
DROP TABLE IF EXISTS public.mentorship_bookings_2026_11 CASCADE;
DROP TABLE IF EXISTS public.mentorship_bookings_2026_12 CASCADE;
DROP TABLE IF EXISTS public.mentorship_bookings_2027_01 CASCADE;
DROP TABLE IF EXISTS public.mentorship_bookings_2027_02 CASCADE;

SELECT '✅ Monthly partition tables dropped' AS status;

-- Drop parent partitioned table
DROP TABLE IF EXISTS public.mentorship_bookings CASCADE;

SELECT '✅ Parent mentorship_bookings table dropped' AS status;

-- ============================================================================
-- STEP 3: Create new single mentorship_bookings table (non-partitioned)
-- ============================================================================

CREATE TABLE public.mentorship_bookings (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Session details
    mentor_id uuid NOT NULL REFERENCES public.mentors(id) ON DELETE CASCADE,
    mentee_id uuid NOT NULL REFERENCES public.members(id) ON DELETE CASCADE,
    session_date timestamptz NOT NULL,
    duration_minutes integer NOT NULL DEFAULT 60,
    session_type text NOT NULL DEFAULT 'one-on-one', -- 'one-on-one', 'group', 'workshop'
    
    -- Status tracking
    status text NOT NULL DEFAULT 'pending', -- 'pending', 'confirmed', 'completed', 'cancelled', 'no-show'
    booking_status text DEFAULT 'pending', -- Legacy field, keep for compatibility
    
    -- Session content
    topic text,
    notes text,
    mentee_goals text,
    mentor_feedback text,
    rating integer CHECK (rating >= 1 AND rating <= 5),
    
    -- Meeting details
    meeting_url text,
    meeting_platform text, -- 'zoom', 'google-meet', 'teams', 'in-person'
    location text, -- For in-person meetings
    
    -- Reminders and notifications
    reminder_sent boolean DEFAULT false,
    confirmation_sent boolean DEFAULT false,
    feedback_requested boolean DEFAULT false,
    
    -- Metadata
    metadata jsonb DEFAULT '{}'::jsonb,
    cancellation_reason text,
    cancelled_by uuid, -- member_id of who cancelled
    cancelled_at timestamptz,
    
    -- Audit fields
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    created_by uuid,
    updated_by uuid
);

-- Add indexes for common queries
CREATE INDEX idx_mentorship_bookings_mentor_id ON public.mentorship_bookings(mentor_id);
CREATE INDEX idx_mentorship_bookings_mentee_id ON public.mentorship_bookings(mentee_id);
CREATE INDEX idx_mentorship_bookings_session_date ON public.mentorship_bookings(session_date);
CREATE INDEX idx_mentorship_bookings_status ON public.mentorship_bookings(status);
CREATE INDEX idx_mentorship_bookings_created_at ON public.mentorship_bookings(created_at);
CREATE INDEX idx_mentorship_bookings_mentor_status ON public.mentorship_bookings(mentor_id, status);
CREATE INDEX idx_mentorship_bookings_mentee_status ON public.mentorship_bookings(mentee_id, status);

-- Add comments for documentation
COMMENT ON TABLE public.mentorship_bookings IS 'Mentorship session bookings - single non-partitioned table for all sessions';
COMMENT ON COLUMN public.mentorship_bookings.session_type IS 'Type of mentorship session: one-on-one, group, workshop';
COMMENT ON COLUMN public.mentorship_bookings.status IS 'Current status: pending, confirmed, completed, cancelled, no-show';
COMMENT ON COLUMN public.mentorship_bookings.rating IS 'Mentee rating of session (1-5 stars)';

SELECT '✅ New mentorship_bookings table created' AS status;

-- ============================================================================
-- STEP 4: Optionally drop old member table backups (after stakeholder approval)
-- ============================================================================

-- DO NOT uncomment these until stakeholder confirms everything works for at least 1 week!

-- DROP TABLE IF EXISTS public.members_old CASCADE;
-- DROP TABLE IF EXISTS public.community_members_old CASCADE;
-- DROP TABLE IF EXISTS public.members_full_old CASCADE;
-- DROP TABLE IF EXISTS public.members_full_orphans CASCADE;

-- SELECT '✅ Old member table backups dropped' AS status;

-- ============================================================================
-- STEP 5: Verify cleanup
-- ============================================================================

-- List all remaining member-related tables
SELECT 
    tablename,
    CASE 
        WHEN tablename LIKE '%_old' THEN 'Backup table (can drop later)'
        WHEN tablename LIKE '%_backup_%' THEN 'Migration backup (can drop after verification)'
        WHEN tablename = 'members' THEN '✅ Active unified table'
        ELSE 'Other'
    END AS table_type
FROM pg_tables 
WHERE schemaname = 'public' 
    AND (tablename LIKE '%member%' OR tablename LIKE '%mentorship_booking%')
ORDER BY tablename;

-- Verify no orphaned constraints
SELECT 
    tc.constraint_name,
    tc.table_name,
    tc.constraint_type
FROM information_schema.table_constraints AS tc
WHERE tc.table_schema = 'public'
    AND (
        tc.constraint_name LIKE '%projects_project%'
        OR tc.constraint_name LIKE '%projects_projectapplication%'
        OR tc.constraint_name LIKE '%mentorship_bookings_202%'
    );

-- Should return 0 rows if cleanup was successful

-- ============================================================================
-- SUMMARY OF CHANGES
-- ============================================================================

SELECT 
    'Cleanup Summary' AS report,
    (SELECT COUNT(*) FROM public.members) AS active_members,
    (SELECT COUNT(*) FROM public.projects) AS active_projects,
    (SELECT COUNT(*) FROM public.project_applications) AS active_applications,
    (SELECT COUNT(*) FROM public.mentorship_bookings) AS active_bookings,
    '✅ All duplicate tables removed' AS status;

-- ============================================================================
-- NEXT STEPS:
-- ============================================================================

-- After verifying cleanup was successful:
-- 1. Update Django models to remove CommunityMember and duplicate Project models
-- 2. Update apps/projects app (delete entire app or remove from INSTALLED_APPS)
-- 3. Run Django migrations to sync with new schema
-- 4. Test all application features
-- 5. After 1 week of stable operation, drop _old backup tables
