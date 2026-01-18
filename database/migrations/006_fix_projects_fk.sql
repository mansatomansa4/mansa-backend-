-- =====================================================
-- FIX PROJECTS FOREIGN KEY CONSTRAINT
-- =====================================================
-- The projects.focal_person_id still references members_old
-- instead of the new unified members table.
-- This script updates the constraint.
-- =====================================================

BEGIN;

-- Step 1: Drop old constraint pointing to members_old
ALTER TABLE projects
    DROP CONSTRAINT IF EXISTS fk_projects_focal_person;

-- Step 2: Add new constraint pointing to members
ALTER TABLE projects
    ADD CONSTRAINT fk_projects_focal_person 
    FOREIGN KEY (focal_person_id) 
    REFERENCES members(id) 
    ON DELETE SET NULL;

-- Step 3: Verify the constraint
SELECT 
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_name = 'projects'
    AND kcu.column_name = 'focal_person_id';

-- Step 4: Check for any orphaned records (should be 0)
SELECT COUNT(*) as orphaned_projects
FROM projects
WHERE focal_person_id IS NOT NULL 
  AND focal_person_id NOT IN (SELECT id FROM members);

COMMIT;

-- =====================================================
-- Expected Result:
-- - Constraint now points to members table
-- - 0 orphaned records
-- =====================================================
