-- ============================================================================
-- FIX: Link project applications to members
-- Purpose: Diagnose and fix member_id linkage issues
-- ============================================================================

-- STEP 1: Diagnose the issue
SELECT 
    'Total applications' AS category,
    COUNT(*) AS count
FROM public.project_applications
UNION ALL
SELECT 
    'Applications with NULL member_id',
    COUNT(*)
FROM public.project_applications
WHERE member_id IS NULL
UNION ALL
SELECT 
    'Applications with valid member link',
    COUNT(*)
FROM public.project_applications pa
WHERE pa.member_id IS NOT NULL
    AND EXISTS (SELECT 1 FROM public.members m WHERE m.id = pa.member_id);

-- ============================================================================

-- STEP 2: Show sample of broken applications
SELECT 
    pa.id AS application_id,
    pa.member_id,
    pa.project_id,
    pa.status,
    pa.created_at,
    CASE 
        WHEN pa.member_id IS NULL THEN '❌ member_id is NULL'
        WHEN NOT EXISTS (SELECT 1 FROM public.members WHERE id = pa.member_id) THEN '❌ member_id does not exist in members table'
        ELSE '✅ Valid'
    END AS status_check
FROM public.project_applications pa
LIMIT 10;

-- ============================================================================

-- STEP 3: Check ALL columns in project_applications table
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' 
    AND table_name = 'project_applications'
ORDER BY ordinal_position;
