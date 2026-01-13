# Supabase Database Setup

## Overview
This Django backend now uses **Supabase PostgreSQL** exclusively as its database. No separate PostgreSQL instance is needed.

## Environment Variables Required

Add these to your Render environment variables (or `.env` file for local development):

### 1. Supabase API Credentials (for mentorship features)
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
```

### 2. Supabase Database Connection
```
SUPABASE_DB_URL=postgresql://postgres.your-project-id:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

## Where to Find These Values

### In Supabase Dashboard:

1. **SUPABASE_URL** & **SUPABASE_SERVICE_KEY**:
   - Go to: Project Settings → API
   - URL: "Project URL"
   - Service Key: "service_role" key (under "Project API keys")

2. **SUPABASE_DB_URL**:
   - Go to: Project Settings → Database
   - Look for "Connection string" → "URI"
   - Choose "Connection pooling" for better performance
   - Copy the full connection string starting with `postgresql://`

## Setting Up on Render

1. Go to your Render dashboard
2. Select your `mansa-backend` service
3. Go to "Environment" tab
4. Add these variables:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`
   - `SUPABASE_DB_URL`
5. Click "Save Changes"
6. Render will automatically redeploy

## Running Migrations

After setting up the database connection, run migrations to create Django tables in Supabase:

```bash
python manage.py migrate
```

## Verifying Connection

To test the database connection:

```bash
python manage.py dbshell
```

This should connect you to your Supabase PostgreSQL database.

## Benefits of This Setup

1. **Single Database**: All data (users, mentorship, projects) in one place
2. **No Separate PostgreSQL**: No need to maintain a separate database instance
3. **Supabase Features**: Can use Supabase realtime, auth, and storage features
4. **Automatic Backups**: Supabase handles database backups
5. **Scalable**: Connection pooling built-in

## Local Development

For local development, create a `.env` file in the project root:

```env
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=true
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_DB_URL=postgresql://postgres.your-project-id:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

## Troubleshooting

### Connection Issues
- Verify the `SUPABASE_DB_URL` is correct
- Ensure SSL is enabled (Supabase requires SSL)
- Check that connection pooling is enabled for better performance

### Migration Errors
- Make sure migrations are run: `python manage.py migrate`
- Check that the database user has CREATE TABLE permissions

### User Not Found
- Ensure users exist in the Supabase `users_user` table (created by Django migrations)
- Run `python manage.py createsuperuser` to create an admin user
