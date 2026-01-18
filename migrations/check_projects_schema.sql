-- ============================================================================
-- DIAGNOSTIC: Check projects table schema
-- ============================================================================

SELECT 
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public' 
    AND table_name = 'projects'
ORDER BY ordinal_position;

-- Sample data
SELECT * FROM public.projects LIMIT 3;
