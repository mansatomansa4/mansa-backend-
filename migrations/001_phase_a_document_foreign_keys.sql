-- ============================================================================
-- PHASE A: DOCUMENT FOREIGN KEY DEPENDENCIES
-- Created: 2026-01-18
-- Purpose: Document all FK relationships to tables being modified
-- ============================================================================

-- Query all foreign keys referencing the tables we're modifying
SELECT
    tc.table_schema,
    tc.table_name AS referencing_table,
    kcu.column_name AS referencing_column,
    ccu.table_schema AS referenced_schema,
    ccu.table_name AS referenced_table,
    ccu.column_name AS referenced_column,
    tc.constraint_name
FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
    AND tc.table_schema='public'
    AND ccu.table_name IN ('members', 'community_members', 'projects', 'project_applications')
ORDER BY ccu.table_name, tc.table_name;

-- Get row counts for tables that reference members
SELECT 
    'project_applications' AS table_name,
    COUNT(*) AS row_count,
    COUNT(DISTINCT member_id) AS distinct_member_ids
FROM public.project_applications
WHERE member_id IS NOT NULL
UNION ALL
SELECT 
    'project_members',
    COUNT(*),
    COUNT(DISTINCT member_id)
FROM public.project_members
WHERE member_id IS NOT NULL
UNION ALL
SELECT 
    'research_cohort_applications',
    COUNT(*),
    COUNT(DISTINCT member_id)
FROM public.research_cohort_applications
WHERE member_id IS NOT NULL
UNION ALL
SELECT 
    'education_cohort_applications',
    COUNT(*),
    COUNT(DISTINCT member_id)
FROM public.education_cohort_applications
WHERE member_id IS NOT NULL;

-- Verify all member_ids in referencing tables exist in members table
SELECT 
    'Orphaned member_ids in project_applications' AS check_type,
    COUNT(*) AS orphaned_count
FROM public.project_applications pa
WHERE pa.member_id IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM public.members m WHERE m.id = pa.member_id);

-- This helps us understand the dependency structure before making changes
