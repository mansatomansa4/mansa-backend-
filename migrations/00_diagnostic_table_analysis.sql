-- Diagnostic Script to Identify Duplicate Tables and Their Data Content
-- Run this in Supabase SQL Editor to assess which tables to keep
-- Created for Database Deduplication Project

-- ============================================================================
-- PART 1: CHECK ROW COUNTS FOR ALL POTENTIAL DUPLICATE TABLES
-- ============================================================================

-- Members-related tables
SELECT 'members' AS table_name, COUNT(*) AS row_count FROM public.members
UNION ALL
SELECT 'community_members', COUNT(*) FROM public.community_members
UNION ALL
SELECT 'members_full', COUNT(*) FROM public.members_full
UNION ALL
SELECT 'members_full_orphans', COUNT(*) FROM public.members_full_orphans

UNION ALL
-- Projects-related tables
SELECT 'projects', COUNT(*) FROM public.projects
UNION ALL
SELECT 'projects_project', COUNT(*) FROM public.projects_project

UNION ALL
-- Project Applications tables
SELECT 'project_applications', COUNT(*) FROM public.project_applications
UNION ALL
SELECT 'projects_projectapplication', COUNT(*) FROM public.projects_projectapplication

UNION ALL
-- Mentorship Bookings tables (partitioned)
SELECT 'mentorship_bookings', COUNT(*) FROM public.mentorship_bookings
UNION ALL
SELECT 'mentorship_bookings_2026_01', COUNT(*) FROM public.mentorship_bookings_2026_01
UNION ALL
SELECT 'mentorship_bookings_2026_02', COUNT(*) FROM public.mentorship_bookings_2026_02
UNION ALL
SELECT 'mentorship_bookings_2026_03', COUNT(*) FROM public.mentorship_bookings_2026_03
UNION ALL
SELECT 'mentorship_bookings_2026_04', COUNT(*) FROM public.mentorship_bookings_2026_04
UNION ALL
SELECT 'mentorship_bookings_2026_05', COUNT(*) FROM public.mentorship_bookings_2026_05
UNION ALL
SELECT 'mentorship_bookings_2026_06', COUNT(*) FROM public.mentorship_bookings_2026_06
UNION ALL
SELECT 'mentorship_bookings_2026_07', COUNT(*) FROM public.mentorship_bookings_2026_07
UNION ALL
SELECT 'mentorship_bookings_2026_08', COUNT(*) FROM public.mentorship_bookings_2026_08
UNION ALL
SELECT 'mentorship_bookings_2026_09', COUNT(*) FROM public.mentorship_bookings_2026_09
UNION ALL
SELECT 'mentorship_bookings_2026_10', COUNT(*) FROM public.mentorship_bookings_2026_10
UNION ALL
SELECT 'mentorship_bookings_2026_11', COUNT(*) FROM public.mentorship_bookings_2026_11
UNION ALL
SELECT 'mentorship_bookings_2026_12', COUNT(*) FROM public.mentorship_bookings_2026_12
UNION ALL
SELECT 'mentorship_bookings_2027_01', COUNT(*) FROM public.mentorship_bookings_2027_01
ORDER BY table_name;

-- ============================================================================
-- PART 2: CHECK FOREIGN KEY RELATIONSHIPS
-- ============================================================================

SELECT
    tc.table_name, 
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
    AND tc.table_schema='public'
    AND tc.table_name IN (
        'members', 'community_members', 'members_full', 'members_full_orphans',
        'projects', 'projects_project',
        'project_applications', 'projects_projectapplication',
        'mentorship_bookings', 'mentorship_bookings_2026_01', 'mentorship_bookings_2026_02',
        'mentorship_bookings_2026_03', 'mentorship_bookings_2026_04', 'mentorship_bookings_2026_05',
        'mentorship_bookings_2026_06', 'mentorship_bookings_2026_07', 'mentorship_bookings_2026_08',
        'mentorship_bookings_2026_09', 'mentorship_bookings_2026_10', 'mentorship_bookings_2026_11',
        'mentorship_bookings_2026_12', 'mentorship_bookings_2027_01'
    )
ORDER BY tc.table_name, kcu.column_name;

-- ============================================================================
-- PART 3: CHECK WHICH TABLES ARE REFERENCED BY OTHER TABLES
-- ============================================================================

SELECT
    ccu.table_name AS referenced_table,
    tc.table_name AS referencing_table,
    kcu.column_name AS referencing_column
FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
    AND tc.table_schema='public'
    AND ccu.table_name IN (
        'members', 'community_members', 'members_full', 'members_full_orphans',
        'projects', 'projects_project',
        'project_applications', 'projects_projectapplication',
        'mentorship_bookings'
    )
ORDER BY ccu.table_name, tc.table_name;

-- ============================================================================
-- PART 4: SAMPLE DATA FROM EACH TABLE GROUP
-- ============================================================================

-- Members sample
SELECT 'members' AS source, id, name, email, created_at FROM public.members LIMIT 3;
SELECT 'community_members' AS source, id, name, email, created_at FROM public.community_members LIMIT 3;

-- Projects sample
SELECT 'projects' AS source, id, title, status, created_at FROM public.projects LIMIT 3;
SELECT 'projects_project' AS source, id, title, status, created_at FROM public.projects_project LIMIT 3;

-- Project Applications sample
SELECT 'project_applications' AS source, id, project_id, applicant_email, status FROM public.project_applications LIMIT 3;
SELECT 'projects_projectapplication' AS source, id, project_id, status FROM public.projects_projectapplication LIMIT 3;

-- Mentorship Bookings sample
SELECT 'mentorship_bookings' AS source, id, mentor_id, session_date, status FROM public.mentorship_bookings LIMIT 3;
SELECT 'mentorship_bookings_2026_01' AS source, id, mentor_id, session_date, status FROM public.mentorship_bookings_2026_01 LIMIT 3;
