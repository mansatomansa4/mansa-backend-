-- ============================================================================
-- PHASE A: UPDATE FOREIGN KEY CONSTRAINTS
-- Created: 2026-01-18
-- Purpose: Update FK constraints to point from old members table to members_new
-- Dependencies: 002_phase_a_merge_members.sql (members_new table created and populated)
-- ============================================================================

-- IMPORTANT: This script updates FK constraints on dependent tables
-- Tables affected: project_applications, project_members, 
--                  research_cohort_applications, education_cohort_applications

-- ============================================================================
-- STEP 1: Drop existing FK constraints on project_applications
-- ============================================================================

-- First, document the existing constraint
SELECT 
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS referenced_table
FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
    AND tc.table_schema='public'
    AND tc.table_name = 'project_applications'
    AND kcu.column_name = 'member_id';

-- Drop the constraint (replace constraint_name with actual name from query above)
DO $$
DECLARE
    constraint_rec RECORD;
BEGIN
    FOR constraint_rec IN 
        SELECT tc.constraint_name
        FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_schema='public'
            AND tc.table_name = 'project_applications'
            AND kcu.column_name = 'member_id'
    LOOP
        EXECUTE 'ALTER TABLE public.project_applications DROP CONSTRAINT ' || constraint_rec.constraint_name;
    END LOOP;
END $$;

-- Add new constraint pointing to members_new
ALTER TABLE public.project_applications
ADD CONSTRAINT fk_project_applications_member_id 
FOREIGN KEY (member_id) REFERENCES public.members_new(id) ON DELETE CASCADE;

-- Verify
SELECT 'project_applications FK updated' AS status;

-- ============================================================================
-- STEP 2: Update FK constraints on project_members
-- ============================================================================

DO $$
DECLARE
    constraint_rec RECORD;
BEGIN
    FOR constraint_rec IN 
        SELECT tc.constraint_name
        FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_schema='public'
            AND tc.table_name = 'project_members'
            AND kcu.column_name = 'member_id'
    LOOP
        EXECUTE 'ALTER TABLE public.project_members DROP CONSTRAINT ' || constraint_rec.constraint_name;
    END LOOP;
END $$;

ALTER TABLE public.project_members
ADD CONSTRAINT fk_project_members_member_id 
FOREIGN KEY (member_id) REFERENCES public.members_new(id) ON DELETE CASCADE;

SELECT 'project_members FK updated' AS status;

-- ============================================================================
-- STEP 3: Update FK constraints on research_cohort_applications
-- ============================================================================

DO $$
DECLARE
    constraint_rec RECORD;
BEGIN
    FOR constraint_rec IN 
        SELECT tc.constraint_name
        FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_schema='public'
            AND tc.table_name = 'research_cohort_applications'
            AND kcu.column_name = 'member_id'
    LOOP
        EXECUTE 'ALTER TABLE public.research_cohort_applications DROP CONSTRAINT ' || constraint_rec.constraint_name;
    END LOOP;
END $$;

ALTER TABLE public.research_cohort_applications
ADD CONSTRAINT fk_research_cohort_applications_member_id 
FOREIGN KEY (member_id) REFERENCES public.members_new(id) ON DELETE CASCADE;

SELECT 'research_cohort_applications FK updated' AS status;

-- ============================================================================
-- STEP 4: Update FK constraints on education_cohort_applications
-- ============================================================================

DO $$
DECLARE
    constraint_rec RECORD;
BEGIN
    FOR constraint_rec IN 
        SELECT tc.constraint_name
        FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_schema='public'
            AND tc.table_name = 'education_cohort_applications'
            AND kcu.column_name = 'member_id'
    LOOP
        EXECUTE 'ALTER TABLE public.education_cohort_applications DROP CONSTRAINT ' || constraint_rec.constraint_name;
    END LOOP;
END $$;

ALTER TABLE public.education_cohort_applications
ADD CONSTRAINT fk_education_cohort_applications_member_id 
FOREIGN KEY (member_id) REFERENCES public.members_new(id) ON DELETE CASCADE;

SELECT 'education_cohort_applications FK updated' AS status;

-- ============================================================================
-- STEP 5: Verify all FK constraints are updated
-- ============================================================================

SELECT 
    tc.table_name AS referencing_table,
    kcu.column_name AS referencing_column,
    ccu.table_name AS referenced_table,
    tc.constraint_name,
    CASE 
        WHEN ccu.table_name = 'members_new' THEN '✅ UPDATED'
        WHEN ccu.table_name = 'members' THEN '❌ STILL POINTS TO OLD TABLE'
        ELSE '⚠️ UNEXPECTED'
    END AS status
FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
    AND tc.table_schema='public'
    AND kcu.column_name = 'member_id'
    AND tc.table_name IN (
        'project_applications',
        'project_members',
        'research_cohort_applications',
        'education_cohort_applications'
    )
ORDER BY tc.table_name;

-- ============================================================================
-- STEP 6: Verify no orphaned records
-- ============================================================================

SELECT 
    'Orphaned records check' AS check_type,
    COUNT(*) AS count,
    CASE 
        WHEN COUNT(*) = 0 THEN '✅ NO ORPHANS'
        ELSE '❌ ORPHANED RECORDS FOUND'
    END AS status
FROM (
    SELECT member_id FROM public.project_applications
    WHERE member_id IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM public.members_new WHERE id = project_applications.member_id)
    UNION ALL
    SELECT member_id FROM public.project_members
    WHERE member_id IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM public.members_new WHERE id = project_members.member_id)
    UNION ALL
    SELECT member_id FROM public.research_cohort_applications
    WHERE member_id IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM public.members_new WHERE id = research_cohort_applications.member_id)
    UNION ALL
    SELECT member_id FROM public.education_cohort_applications
    WHERE member_id IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM public.members_new WHERE id = education_cohort_applications.member_id)
) orphan_check;

-- ============================================================================
-- NEXT STEPS (Run in separate script after verification):
-- ============================================================================

-- After verifying all FK constraints are updated correctly:
-- 1. Run atomic table rename script (004_phase_a_atomic_rename.sql)
-- 2. Run cleanup script (005_phase_a_cleanup.sql)

-- DO NOT proceed until stakeholder verifies:
-- ✅ All 4 FK constraints show 'UPDATED' status
-- ✅ No orphaned records found
