-- =====================================================
-- PHASE A ROLLBACK SCRIPT
-- =====================================================
-- This script provides a way to rollback the Phase A database deduplication
-- changes if needed. Only run this if you encounter critical issues and
-- need to restore the previous table structure.
--
-- IMPORTANT: This should only be run after consulting with the team and
-- ensuring all applications are stopped to prevent data inconsistencies.
-- =====================================================

BEGIN;

-- Step 1: Verify backup tables exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_tables WHERE tablename = 'members_old') THEN
        RAISE EXCEPTION 'Backup table members_old not found. Cannot proceed with rollback.';
    END IF;
    
    IF NOT EXISTS (SELECT FROM pg_tables WHERE tablename = 'community_members_old') THEN
        RAISE EXCEPTION 'Backup table community_members_old not found. Cannot proceed with rollback.';
    END IF;
END $$;

-- Step 2: Drop current members table and restore from backup
ALTER TABLE members RENAME TO members_unified;
ALTER TABLE members_old RENAME TO members;

-- Step 3: Restore community_members table
ALTER TABLE community_members_old RENAME TO community_members;

-- Step 4: Update foreign key constraints to point back to original members table
-- Note: This assumes the original FK structure - adjust if needed

-- project_applications
ALTER TABLE project_applications
    DROP CONSTRAINT IF EXISTS project_applications_member_id_fkey,
    ADD CONSTRAINT project_applications_member_id_fkey 
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE SET NULL;

-- project_members
ALTER TABLE project_members
    DROP CONSTRAINT IF EXISTS project_members_member_id_fkey,
    ADD CONSTRAINT project_members_member_id_fkey 
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE;

-- research_cohort_applications
ALTER TABLE research_cohort_applications
    DROP CONSTRAINT IF EXISTS research_cohort_applications_member_id_fkey,
    ADD CONSTRAINT research_cohort_applications_member_id_fkey 
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE;

-- education_cohort_applications
ALTER TABLE education_cohort_applications
    DROP CONSTRAINT IF EXISTS education_cohort_applications_member_id_fkey,
    ADD CONSTRAINT education_cohort_applications_member_id_fkey 
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE;

-- Step 5: Verify rollback
SELECT 
    'members' as table_name, 
    COUNT(*) as row_count,
    'Should be 131' as expected
FROM members
UNION ALL
SELECT 
    'community_members' as table_name, 
    COUNT(*) as row_count,
    'Should be 131' as expected
FROM community_members
UNION ALL
SELECT 
    'members_unified' as table_name, 
    COUNT(*) as row_count,
    'New unified table (can be dropped)' as expected
FROM members_unified;

-- Step 6: Check foreign key constraints
SELECT
    tc.table_name,
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND ccu.table_name = 'members'
ORDER BY tc.table_name;

COMMIT;

-- =====================================================
-- POST-ROLLBACK CLEANUP (OPTIONAL)
-- =====================================================
-- After confirming rollback is successful, you may want to drop the
-- unified table to clean up:
-- 
-- DROP TABLE IF EXISTS members_unified;
-- 
-- =====================================================
-- DJANGO CODE ROLLBACK REQUIRED
-- =====================================================
-- Remember to also revert the Django code changes:
-- 1. Restore CommunityMember model in apps/platform/models.py
-- 2. Restore CommunityMemberSerializer and ViewSet
-- 3. Re-enable apps.projects in INSTALLED_APPS if needed
-- 4. Revert apps.core.analytics import back to apps.projects
-- 5. Run: python manage.py migrate --fake
-- =====================================================
