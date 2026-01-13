# URGENT: Render Environment Setup Required

## ⚠️ Action Required on Render

Your backend has been migrated to use **Supabase PostgreSQL exclusively**. You need to add one new environment variable to Render:

### Step-by-Step Instructions:

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Select your service**: `mansa-backend-1rr8`
3. **Click "Environment"** tab on the left
4. **Add this new variable**:

```
SUPABASE_DB_URL
```

**Value**: Get from Supabase Dashboard:
- Go to your Supabase project: https://supabase.com/dashboard/project/[your-project-id]
- Click "Project Settings" (gear icon) → "Database"
- Under "Connection string" section, click "URI"
- **Enable "Use connection pooling"** (recommended for production)
- Copy the connection string (starts with `postgresql://postgres...`)
- **IMPORTANT**: Replace `[YOUR-PASSWORD]` with your actual database password

Example format:
```
postgresql://postgres.abcdefghijk:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

5. **Verify existing variables are set**:
   - ✅ `SUPABASE_URL` (should be like `https://abcdefghijk.supabase.co`)
   - ✅ `SUPABASE_SERVICE_KEY` (long key starting with `eyJ...`)

6. **Click "Save Changes"**
7. Render will automatically redeploy (takes ~2-3 minutes)

## What Changed?

**Before**: Django used a separate PostgreSQL database on Render
**Now**: Django connects directly to Supabase PostgreSQL

**Benefits**:
- ✅ Single database for all data
- ✅ Users table accessible by both Django and Supabase
- ✅ No more "email not found" issues
- ✅ Simpler architecture
- ✅ Automatic backups via Supabase

## After Deployment

Once Render finishes deploying:

1. **Run migrations** (Render should do this automatically, but verify):
   - In Render dashboard, go to "Shell" tab
   - Run: `python manage.py migrate`

2. **Test login** at: https://www.mansa-to-mansa.org/community/mentorship/auth

## Need Your Supabase Database Password?

If you don't have your Supabase database password:

1. Go to Supabase Dashboard → Project Settings → Database
2. Click "Reset database password"
3. Copy the new password
4. Use it in the `SUPABASE_DB_URL` connection string

## Verification

After deployment, check Render logs for:
```
✅ "Supabase client initialized successfully"
✅ No "Not Found: /api/users/email-login/" errors
✅ Database migrations applied successfully
```

## Support

If you need help:
1. Check Render logs for errors
2. Verify all 3 environment variables are set correctly
3. Ensure the SUPABASE_DB_URL password is correct
