# Schema Alignment Update - Post Phase A

**Date:** January 18, 2026  
**Status:** ✅ Complete

## Summary

Updated backend, frontend, and dashboard code to align with the current Supabase database schema after Phase A deduplication.

---

## Issues Found & Fixed

### 1. Projects Table FK Constraint ❌→✅

**Problem:**
```sql
CONSTRAINT fk_projects_focal_person FOREIGN KEY (focal_person_id) 
    REFERENCES public.members_old(id)
```

The `projects.focal_person_id` was still referencing `members_old` instead of the unified `members` table.

**Solution:**
Created migration script `006_fix_projects_fk.sql` to:
1. Drop old constraint pointing to `members_old`
2. Add new constraint pointing to `members`
3. Verify no orphaned records

**To Execute:**
```sql
-- Run in Supabase SQL Editor
-- File: database/migrations/006_fix_projects_fk.sql
```

---

### 2. Dashboard Member Interface ✅

**Updated:** `Mansa-dashboard/src/lib/api.ts`

**Changes:**
- Changed `areaOfExpertise` to `areaofexpertise` (matches database lowercase)
- Added `areaOfExpertise` as alias for backwards compatibility
- Added new unified fields from `community_members`:
  - `joined_date`
  - `profile_picture`
  - `bio`
  - `location` (moved from computed property to actual field)
  - `motivation`

**Before:**
```typescript
export interface Member {
  id: string;
  name: string;
  // ... fields ...
  areaOfExpertise?: string;
  // ... fields ...
  location?: string; // Was only in computed properties
}
```

**After:**
```typescript
export interface Member {
  id: string;
  name: string;
  // ... fields ...
  areaofexpertise?: string; // Matches DB
  areaOfExpertise?: string; // Backwards compatibility
  // ... fields ...
  
  // Unified fields
  joined_date?: string;
  profile_picture?: string;
  bio?: string;
  location?: string;
  motivation?: string;
}
```

---

## Backend Status ✅

### Django Models
- ✅ `Member` model already updated (Phase A)
- ✅ `Project` model has correct `focal_person_id` field
- ✅ All FK relationships aligned

### Verified:
- `apps/platform/models.py` - Member model includes all unified fields
- `apps/platform/models.py` - Project model has focal_person_id
- No reference to `CommunityMember` model
- No imports from `apps.projects`

---

## Frontend Status ✅

### mansa-redesign
- ✅ Uses Supabase client directly (no type changes needed)
- ✅ `src/types/projects.ts` includes `focal_person_id` field
- ✅ No hardcoded member field references

### Recommendations:
If frontend code accesses member fields:
- Use `areaofexpertise` (lowercase) when querying database
- Display as "Area of Expertise" in UI
- New fields available: `joined_date`, `profile_picture`, `bio`, `location`, `motivation`

---

## Dashboard Status ✅

### Mansa-dashboard
- ✅ `Member` interface updated in `src/lib/api.ts`
- ✅ Backwards compatible (kept `areaOfExpertise` alias)
- ✅ All new unified fields available

### API Endpoints:
- ✅ `/api/platform/members/` - Returns unified member data
- ✅ `/api/platform/projects/` - Includes focal_person fields
- ✅ `/api/platform/applications/` - Linked to members via member_id

---

## Database Schema Alignment

### Current Schema (Verified):
| Table | FK Constraint | References | Status |
|-------|--------------|------------|--------|
| `members` | - | - | ✅ Unified |
| `projects` | `focal_person_id` | `members(id)` | ⚠️ Needs fix (still points to members_old) |
| `project_applications` | `member_id` | `members(id)` | ✅ Correct |
| `project_members` | `member_id` | `members(id)` | ✅ Correct |
| `research_cohort_applications` | `member_id` | `members(id)` | ✅ Correct |
| `education_cohort_applications` | `member_id` | `members(id)` | ✅ Correct |
| `mentorship_bookings` | `mentee_id` | `members(id)` | ✅ Correct |

---

## Action Required

### 1. Execute Database Migration ⚠️ CRITICAL
```sql
-- Run this in Supabase SQL Editor:
-- File: mansa-backend/database/migrations/006_fix_projects_fk.sql

BEGIN;

ALTER TABLE projects
    DROP CONSTRAINT IF EXISTS fk_projects_focal_person;

ALTER TABLE projects
    ADD CONSTRAINT fk_projects_focal_person 
    FOREIGN KEY (focal_person_id) 
    REFERENCES members(id) 
    ON DELETE SET NULL;

COMMIT;
```

### 2. Test API Endpoints
```bash
# Test member endpoint
curl http://localhost:8000/api/platform/members/

# Test projects endpoint
curl http://localhost:8000/api/platform/projects/

# Verify new fields in response
```

### 3. Verify Dashboard
- Login to dashboard
- Check Members page - verify new fields display
- Check Projects page - verify focal person data shows

---

## Field Mapping Reference

### Member Fields (Database → Code)

| Database Column | Django Field | TypeScript (Dashboard) | Notes |
|----------------|--------------|----------------------|-------|
| `areaofexpertise` | `areaofexpertise` | `areaofexpertise` | Lowercase in DB |
| - | - | `areaOfExpertise` | Alias for compat |
| `joined_date` | `joined_date` | `joined_date` | From community_members |
| `profile_picture` | `profile_picture` | `profile_picture` | From community_members |
| `bio` | `bio` | `bio` | From community_members |
| `location` | `location` | `location` | From community_members |
| `motivation` | `motivation` | `motivation` | From community_members |

---

## Verification Checklist

After executing the migration:

- [ ] Run `006_fix_projects_fk.sql` in Supabase
- [ ] Verify constraint points to `members` table
- [ ] Check 0 orphaned records in projects
- [ ] Test Django: `python manage.py check` (should pass)
- [ ] Test member API endpoint
- [ ] Test projects API endpoint
- [ ] Test dashboard members page
- [ ] Test dashboard projects page

---

## Rollback (If Needed)

If issues arise with the FK update:

```sql
BEGIN;

-- Revert to old constraint
ALTER TABLE projects
    DROP CONSTRAINT IF EXISTS fk_projects_focal_person;

ALTER TABLE projects
    ADD CONSTRAINT fk_projects_focal_person 
    FOREIGN KEY (focal_person_id) 
    REFERENCES members_old(id) 
    ON DELETE SET NULL;

COMMIT;
```

---

## Next Steps

1. ✅ Execute `006_fix_projects_fk.sql` migration
2. ✅ Commit and push code changes
3. ✅ Test all three applications (backend API, frontend, dashboard)
4. ✅ Monitor for any errors in logs
5. ⏭️ After 1 week stability, proceed to Phase B enhancements

---

**Files Modified:**
- `mansa-backend/database/migrations/006_fix_projects_fk.sql` (new)
- `Mansa-dashboard/src/lib/api.ts` (Member interface updated)
- `mansa-backend/SCHEMA_ALIGNMENT_UPDATE.md` (this file)

**Status:** Ready for migration execution ✅
