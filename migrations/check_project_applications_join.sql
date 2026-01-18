-- ============================================================================
-- DIAGNOSTIC: Check project_applications table schema and sample data
-- ============================================================================

-- Get column structure
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' 
    AND table_name = 'project_applications'
ORDER BY ordinal_position;

-- Sample data to see actual values
SELECT * FROM public.project_applications LIMIT 5;

-- Check if project_id values exist in projects table
SELECT 
    pa.id AS application_id,
    pa.project_id,
    pa.member_id,
    pa.status,
    p.id AS matching_project_id,
    p.title AS project_title
FROM public.project_applications pa
LEFT JOIN public.projects p ON pa.project_id = p.id
LIMIT 10;
