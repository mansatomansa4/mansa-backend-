-- ============================================================================
-- FIX: Update member_id in project_applications by matching email
-- ============================================================================

-- STEP 1: See how many applications can be matched
SELECT 
    'Total applications' AS category,
    COUNT(*) AS count
FROM public.project_applications
UNION ALL
SELECT 
    'Currently have member_id',
    COUNT(*)
FROM public.project_applications
WHERE member_id IS NOT NULL
UNION ALL
SELECT 
    'Can be matched by email',
    COUNT(*)
FROM public.project_applications pa
WHERE pa.member_id IS NULL
    AND EXISTS (
        SELECT 1 FROM public.members m 
        WHERE LOWER(TRIM(m.email)) = LOWER(TRIM(pa.applicant_email))
    );

-- ============================================================================

-- STEP 2: UPDATE - Link applications to members by matching email
-- This will update NULL member_id values where we can find matching email
UPDATE public.project_applications pa
SET member_id = m.id
FROM public.members m
WHERE pa.member_id IS NULL
    AND LOWER(TRIM(m.email)) = LOWER(TRIM(pa.applicant_email));

-- ============================================================================

-- STEP 3: Verify the fix
SELECT 
    'After Fix: Total applications' AS category,
    COUNT(*) AS count
FROM public.project_applications
UNION ALL
SELECT 
    'After Fix: Applications with member_id',
    COUNT(*)
FROM public.project_applications
WHERE member_id IS NOT NULL
UNION ALL
SELECT 
    'After Fix: Applications still unmatched',
    COUNT(*)
FROM public.project_applications
WHERE member_id IS NULL;

-- ============================================================================

-- STEP 4: Show sample of fixed applications
SELECT 
    pa.id,
    pa.applicant_name,
    pa.applicant_email,
    m.name AS matched_member_name,
    m.email AS matched_member_email,
    pa.member_id,
    CASE 
        WHEN pa.member_id IS NOT NULL THEN '✅ Linked'
        ELSE '❌ Not matched'
    END AS link_status
FROM public.project_applications pa
LEFT JOIN public.members m ON pa.member_id = m.id
ORDER BY pa.created_at DESC
LIMIT 10;
