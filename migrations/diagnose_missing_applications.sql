-- ============================================================================
-- DIAGNOSTIC: Why are only 2 applications showing?
-- ============================================================================

-- Check how many applications have member_id values
SELECT 
    'Total applications' AS category,
    COUNT(*) AS count
FROM public.project_applications
UNION ALL
SELECT 
    'Applications with member_id',
    COUNT(*)
FROM public.project_applications
WHERE member_id IS NOT NULL
UNION ALL
SELECT 
    'Applications with matching members',
    COUNT(*)
FROM public.project_applications pa
INNER JOIN public.members m ON pa.member_id = m.id;

-- ============================================================================

-- Show applications that DON'T have matching members
SELECT 
    pa.id,
    pa.member_id,
    pa.project_id,
    pa.status,
    pa.created_at,
    CASE 
        WHEN pa.member_id IS NULL THEN '❌ No member_id'
        WHEN NOT EXISTS (SELECT 1 FROM public.members WHERE id = pa.member_id) THEN '❌ member_id not in members table'
        ELSE '✅ Valid'
    END AS issue
FROM public.project_applications pa
ORDER BY pa.created_at DESC
LIMIT 20;
