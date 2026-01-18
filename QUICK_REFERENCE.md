# Phase A Migration - Quick Reference

## ✅ What Changed

### Database
- `members` + `community_members` → unified `members` table (131 rows)
- 18 duplicate/empty tables dropped
- New single `mentorship_bookings` table created
- All foreign keys updated to point to new `members` table

### Django Code
- `apps.projects` removed from INSTALLED_APPS
- `CommunityMember` model removed
- `Member` model updated with all unified fields
- All imports updated to use `apps.platform.models`

### API Endpoints
- ❌ `/api/community-members/` - REMOVED
- ✅ `/api/platform/members/` - Use this instead

---

## 🔍 How to Verify

Run verification script in Supabase SQL Editor:
```sql
-- Located at: database/migrations/verify_phase_a.sql
-- Should show all ✅ PASS results
```

Or check Django:
```bash
python manage.py check
# Should show: System check identified no issues (0 silenced).
```

---

## 🚨 If Something Breaks

### Quick Checks
1. Check if frontend/dashboard is calling old endpoints:
   - `/api/community-members/` → use `/api/platform/members/`
   
2. Check for Django import errors:
   - `from apps.projects.models` → use `apps.platform.models`
   - `CommunityMember` → use `Member` instead

3. Check database connection works:
   ```bash
   python manage.py shell
   >>> from apps.platform.models import Member
   >>> Member.objects.count()
   131
   ```

### Rollback (Last Resort)
If critical issues arise:
1. Stop all applications
2. Run `database/migrations/rollback_phase_a.sql` in Supabase
3. Revert Django code changes (see commit history)
4. Contact team lead

---

## 📊 Current Database State

| Table | Rows | Notes |
|-------|------|-------|
| `members` | 131 | Unified table with all fields |
| `projects` | 17 | Active projects |
| `project_applications` | 41 | All linked to members |
| `mentorship_bookings` | 0 | New empty table |

---

## 📝 Files Created

### Documentation
- `DATABASE_SCHEMA_PHASE_A.md` - Full schema reference
- `PHASE_A_COMPLETE.md` - Implementation summary
- `QUICK_REFERENCE.md` - This file

### Scripts
- `rollback_phase_a.sql` - Rollback procedure
- `verify_phase_a.sql` - Verification tests

---

## 🔄 What's Next

### Immediate (24 hours)
- Monitor application logs
- Test user registration and project applications
- Verify admin dashboard works

### Short term (1 week)
- Keep backup tables for safety
- Gather feedback
- Monitor performance

### After 1 week
- Drop backup tables to free space
- Plan Phase B (audit logs, soft deletes, indexes)

---

## 💡 Tips

### For Developers
- Always use `apps.platform.models.Member` (not CommunityMember)
- Use `/api/platform/members/` endpoint
- `member.areaofexpertise` (lowercase) in Python matches DB

### For Testing
```python
# Get all members
from apps.platform.models import Member
members = Member.objects.all()

# Get member's applications
from apps.platform.models import ProjectApplication
apps = ProjectApplication.objects.filter(member_id='<uuid>')

# Query with joins works
Member.objects.filter(
    id__in=ProjectApplication.objects.values_list('member_id', flat=True)
)
```

---

## 📞 Support

- Documentation: `DATABASE_SCHEMA_PHASE_A.md`
- Verification: Run `verify_phase_a.sql`
- Issues: Check commit history for changes
- Rollback: `rollback_phase_a.sql` (backup tables exist)

---

**Status:** ✅ Production Ready  
**Date:** January 18, 2026  
**All Tests:** PASSED ✅
