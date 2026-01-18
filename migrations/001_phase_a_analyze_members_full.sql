-- ============================================================================
-- PHASE A: ANALYZE MEMBERS_FULL FOR UNIQUE RECORDS
-- Created: 2026-01-18
-- Purpose: Identify if members_full contains unique records not in members
-- ============================================================================

-- Check which IDs are in members_full but NOT in members
SELECT 
    'Records in members_full but NOT in members' AS analysis,
    COUNT(*) AS count
FROM public.members_full mf
WHERE NOT EXISTS (
    SELECT 1 FROM public.members m WHERE m.id = mf.id
);

-- Show the actual records that are unique to members_full
SELECT 
    'Unique records in members_full' AS type,
    mf.*
FROM public.members_full mf
WHERE NOT EXISTS (
    SELECT 1 FROM public.members m WHERE m.id = mf.id
);

-- Compare field values for records that exist in both tables
SELECT 
    'Field comparison for matching IDs' AS type,
    m.id,
    m.name AS members_name,
    mf.name AS members_full_name,
    m.email AS members_email,
    mf.email AS members_full_email,
    m.created_at AS members_created,
    mf.created_at AS members_full_created
FROM public.members m
INNER JOIN public.members_full mf ON m.id = mf.id
LIMIT 5;

-- Summary statistics
SELECT 
    'Summary' AS analysis,
    (SELECT COUNT(*) FROM public.members) AS members_count,
    (SELECT COUNT(*) FROM public.members_full) AS members_full_count,
    (SELECT COUNT(*) FROM public.members_full mf 
     WHERE NOT EXISTS (SELECT 1 FROM public.members m WHERE m.id = mf.id)) AS unique_to_members_full,
    (SELECT COUNT(*) FROM public.members m 
     WHERE NOT EXISTS (SELECT 1 FROM public.members_full mf WHERE mf.id = m.id)) AS unique_to_members;

-- Expected outcome:
-- If unique_to_members_full = 0, then all members_full data is already in members
-- If unique_to_members_full > 0, those records need to be migrated
