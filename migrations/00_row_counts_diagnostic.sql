-- Simplified Row Count Diagnostic - Run this SINGLE query
-- This will show all row counts in one result table

SELECT 'members' AS table_name, COUNT(*) AS row_count FROM public.members
UNION ALL
SELECT 'community_members', COUNT(*) FROM public.community_members
UNION ALL
SELECT 'members_full', COUNT(*) FROM public.members_full
UNION ALL
SELECT 'members_full_orphans', COUNT(*) FROM public.members_full_orphans
UNION ALL
SELECT 'projects', COUNT(*) FROM public.projects
UNION ALL
SELECT 'projects_project', COUNT(*) FROM public.projects_project
UNION ALL
SELECT 'project_applications', COUNT(*) FROM public.project_applications
UNION ALL
SELECT 'projects_projectapplication', COUNT(*) FROM public.projects_projectapplication
UNION ALL
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
