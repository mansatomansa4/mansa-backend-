-- ============================================================================
-- QUERY: Members with their Project Applications
-- Purpose: Get all members with names, emails, phone numbers and projects applied to
-- ============================================================================

-- Option 1: ALL MEMBERS (even those without applications)
SELECT 
    m.name AS member_name,
    m.email AS member_email,
    m.phone AS member_phone,
    m.country,
    m.city,
    p.title AS project_title,
    pa.status AS application_status,
    pa.created_at::date AS application_date
FROM public.members m
LEFT JOIN public.project_applications pa ON m.id = pa.member_id
LEFT JOIN public.projects p ON pa.project_id = p.id
ORDER BY m.name, pa.created_at DESC;

-- ============================================================================

-- Option 2: ONLY members with applications
SELECT 
    m.name AS member_name,
    m.email AS member_email,
    m.phone AS member_phone,
    m.country,
    m.city,
    p.title AS project_title,
    pa.status AS application_status,
    pa.created_at::date AS application_date
FROM public.members m
INNER JOIN public.project_applications pa ON m.id = pa.member_id
INNER JOIN public.projects p ON pa.project_id = p.id
ORDER BY m.name, pa.created_at DESC;

-- ============================================================================

-- Option 3: Summary - Count of applications per member
SELECT 
    m.name AS member_name,
    m.email AS member_email,
    m.phone AS member_phone,
    m.country,
    COUNT(pa.id) AS total_applications
FROM public.members m
LEFT JOIN public.project_applications pa ON m.id = pa.member_id
GROUP BY m.name, m.email, m.phone, m.country
ORDER BY total_applications DESC, m.name;
