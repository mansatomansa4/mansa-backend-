-- ============================================================================
-- DIAGNOSTIC: Get actual schema of members and community_members tables
-- Purpose: Understand the actual column structure before migration
-- ============================================================================

-- Get all columns from members table
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public' 
    AND table_name = 'members'
ORDER BY ordinal_position;

-- Get all columns from community_members table  
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public' 
    AND table_name = 'community_members'
ORDER BY ordinal_position;

-- Sample data from members
SELECT * FROM public.members LIMIT 3;

-- Sample data from community_members
SELECT * FROM public.community_members LIMIT 3;
