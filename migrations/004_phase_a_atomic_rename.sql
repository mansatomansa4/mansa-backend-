-- ============================================================================
-- PHASE A: ATOMIC TABLE RENAME
-- Created: 2026-01-18
-- Purpose: Atomically swap old members table with new unified table
-- Dependencies: 003_phase_a_update_foreign_keys.sql (all FKs updated)
-- ============================================================================

-- IMPORTANT: This script performs atomic table renames
-- The entire operation happens in a single transaction to minimize downtime

BEGIN;

-- ============================================================================
-- STEP 1: Rename old tables for backup/archival
-- ============================================================================

-- Rename members to members_old
ALTER TABLE public.members RENAME TO members_old;

-- Rename community_members to community_members_old
ALTER TABLE public.community_members RENAME TO community_members_old;

-- Rename members_full to members_full_old (if it exists)
ALTER TABLE IF EXISTS public.members_full RENAME TO members_full_old;

SELECT 'Old tables renamed to _old suffix' AS status;

-- ============================================================================
-- STEP 2: Rename members_new to members
-- ============================================================================

ALTER TABLE public.members_new RENAME TO members;

SELECT 'members_new renamed to members' AS status;

-- ============================================================================
-- STEP 3: Update index names to remove _new suffix
-- ============================================================================

-- First, rename old table indexes to avoid conflicts
ALTER INDEX IF EXISTS idx_members_email RENAME TO idx_members_old_email;
ALTER INDEX IF EXISTS idx_members_is_active RENAME TO idx_members_old_is_active;
ALTER INDEX IF EXISTS idx_members_country RENAME TO idx_members_old_country;
ALTER INDEX IF EXISTS idx_members_membershiptype RENAME TO idx_members_old_membershiptype;
ALTER INDEX IF EXISTS idx_members_created_at RENAME TO idx_members_old_created_at;
ALTER INDEX IF EXISTS idx_members_name RENAME TO idx_members_old_name;

-- Now rename new table indexes
ALTER INDEX IF EXISTS idx_members_new_email RENAME TO idx_members_email;
ALTER INDEX IF EXISTS idx_members_new_is_active RENAME TO idx_members_is_active;
ALTER INDEX IF EXISTS idx_members_new_country RENAME TO idx_members_country;
ALTER INDEX IF EXISTS idx_members_new_membershiptype RENAME TO idx_members_membershiptype;
ALTER INDEX IF EXISTS idx_members_new_created_at RENAME TO idx_members_created_at;
ALTER INDEX IF EXISTS idx_members_new_name RENAME TO idx_members_name;

SELECT 'Index names updated' AS status;

-- ============================================================================
-- STEP 4: Verify the swap was successful
-- ============================================================================

SELECT 
    'Verification' AS check_type,
    (SELECT COUNT(*) FROM public.members) AS members_count,
    (SELECT COUNT(*) FROM public.members_old) AS members_old_count,
    (SELECT COUNT(*) FROM public.community_members_old) AS community_members_old_count,
    CASE 
        WHEN (SELECT COUNT(*) FROM public.members) = (SELECT COUNT(*) FROM public.members_old)
        THEN '✅ ROW COUNTS MATCH'
        ELSE '❌ ROW COUNT MISMATCH'
    END AS status;

-- ============================================================================
-- STEP 5: Verify FK constraints point to new table
-- ============================================================================

SELECT 
    tc.table_name AS referencing_table,
    kcu.column_name AS referencing_column,
    ccu.table_name AS referenced_table,
    CASE 
        WHEN ccu.table_name = 'members' THEN '✅ CORRECT'
        ELSE '❌ WRONG TABLE: ' || ccu.table_name
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
-- STEP 6: Test a sample query to ensure everything works
-- ============================================================================

-- Sample query joining members with project_applications
SELECT 
    m.id,
    m.email,
    m.name,
    m.country,
    COUNT(pa.id) AS application_count
FROM public.members m
LEFT JOIN public.project_applications pa ON pa.member_id = m.id
GROUP BY m.id, m.email, m.name, m.country
LIMIT 5;

-- If this query runs successfully, the swap worked!

COMMIT;

-- ============================================================================
-- POST-COMMIT VERIFICATION
-- ============================================================================

-- Run this after COMMIT to confirm everything is correct
SELECT 
    'Post-swap verification' AS report,
    (SELECT COUNT(*) FROM public.members) AS active_members_count,
    (SELECT COUNT(*) FROM public.members WHERE country IS NOT NULL) AS members_with_location,
    (SELECT COUNT(*) FROM public.project_applications WHERE member_id IS NOT NULL) AS applications_with_member_ids,
    (SELECT 
        CASE 
            WHEN COUNT(*) = 0 THEN '✅ NO ORPHANS'
            ELSE '❌ ' || COUNT(*) || ' ORPHANS FOUND'
        END
     FROM public.project_applications pa
     WHERE pa.member_id IS NOT NULL
         AND NOT EXISTS (SELECT 1 FROM public.members m WHERE m.id = pa.member_id)
    ) AS orphan_check;

-- ============================================================================
-- ROLLBACK INSTRUCTIONS (if needed)
-- ============================================================================

-- If something goes wrong during the transaction, it will automatically rollback
-- If you need to manually rollback after commit:
--
-- BEGIN;
-- ALTER TABLE public.members RENAME TO members_failed;
-- ALTER TABLE public.members_old RENAME TO members;
-- ALTER TABLE public.community_members_old RENAME TO community_members;
-- ALTER TABLE IF EXISTS public.members_full_old RENAME TO members_full;
-- COMMIT;
--
-- Then re-run the FK update script to point back to the old tables

-- ============================================================================
-- NEXT STEPS:
-- ============================================================================

-- After verifying the swap was successful:
-- 1. Run cleanup script to drop empty duplicate tables (005_phase_a_cleanup.sql)
-- 2. Update Django models (manual code changes)
-- 3. Update Django migrations (manual code changes)
