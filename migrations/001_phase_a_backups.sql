-- ============================================================================
-- PHASE A: BACKUP TABLES BEFORE MIGRATION
-- Created: 2026-01-18
-- Purpose: Create backup copies of all tables that will be modified
-- ============================================================================

-- This script creates backup copies of all tables before making any changes
-- These backups allow for complete rollback if needed

-- Backup members table
CREATE TABLE IF NOT EXISTS public.members_backup_20260118 AS 
SELECT * FROM public.members;

-- Backup community_members table
CREATE TABLE IF NOT EXISTS public.community_members_backup_20260118 AS 
SELECT * FROM public.community_members;

-- Backup members_full table
CREATE TABLE IF NOT EXISTS public.members_full_backup_20260118 AS 
SELECT * FROM public.members_full;

-- Backup projects table
CREATE TABLE IF NOT EXISTS public.projects_backup_20260118 AS 
SELECT * FROM public.projects;

-- Backup project_applications table
CREATE TABLE IF NOT EXISTS public.project_applications_backup_20260118 AS 
SELECT * FROM public.project_applications;

-- Verify backup row counts
SELECT 
    'members_backup_20260118' AS backup_table,
    (SELECT COUNT(*) FROM public.members) AS original_count,
    (SELECT COUNT(*) FROM public.members_backup_20260118) AS backup_count,
    CASE 
        WHEN (SELECT COUNT(*) FROM public.members) = (SELECT COUNT(*) FROM public.members_backup_20260118) 
        THEN '✅ MATCH' 
        ELSE '❌ MISMATCH' 
    END AS status
UNION ALL
SELECT 
    'community_members_backup_20260118',
    (SELECT COUNT(*) FROM public.community_members),
    (SELECT COUNT(*) FROM public.community_members_backup_20260118),
    CASE 
        WHEN (SELECT COUNT(*) FROM public.community_members) = (SELECT COUNT(*) FROM public.community_members_backup_20260118) 
        THEN '✅ MATCH' 
        ELSE '❌ MISMATCH' 
    END
UNION ALL
SELECT 
    'members_full_backup_20260118',
    (SELECT COUNT(*) FROM public.members_full),
    (SELECT COUNT(*) FROM public.members_full_backup_20260118),
    CASE 
        WHEN (SELECT COUNT(*) FROM public.members_full) = (SELECT COUNT(*) FROM public.members_full_backup_20260118) 
        THEN '✅ MATCH' 
        ELSE '❌ MISMATCH' 
    END
UNION ALL
SELECT 
    'projects_backup_20260118',
    (SELECT COUNT(*) FROM public.projects),
    (SELECT COUNT(*) FROM public.projects_backup_20260118),
    CASE 
        WHEN (SELECT COUNT(*) FROM public.projects) = (SELECT COUNT(*) FROM public.projects_backup_20260118) 
        THEN '✅ MATCH' 
        ELSE '❌ MISMATCH' 
    END
UNION ALL
SELECT 
    'project_applications_backup_20260118',
    (SELECT COUNT(*) FROM public.project_applications),
    (SELECT COUNT(*) FROM public.project_applications_backup_20260118),
    CASE 
        WHEN (SELECT COUNT(*) FROM public.project_applications) = (SELECT COUNT(*) FROM public.project_applications_backup_20260118) 
        THEN '✅ MATCH' 
        ELSE '❌ MISMATCH' 
    END;

-- Expected results:
-- members_backup_20260118: 131 rows
-- community_members_backup_20260118: 131 rows
-- members_full_backup_20260118: 14 rows
-- projects_backup_20260118: 17 rows
-- project_applications_backup_20260118: 41 rows
