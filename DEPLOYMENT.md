# Deployment Guide for Render

## Prerequisites

1. A PostgreSQL database (create one in Render or use external)
2. A Render account

## Render Configuration

### Build Command
```bash
./build.sh
```

### Start Command
```bash
gunicorn config.wsgi:application -c gunicorn.conf.py
```

## Required Environment Variables

Set these in your Render service's Environment Variables:

### Required
- `DATABASE_URL` - PostgreSQL connection string (format: `postgresql://user:password@host:5432/dbname`)
  - **IMPORTANT**: If using Render PostgreSQL, copy the "Internal Database URL" from your database settings
- `DJANGO_SECRET_KEY` - Django secret key (generate a secure random string)
- `DJANGO_ALLOWED_HOSTS` - Comma-separated list of allowed hosts (e.g., `your-app.onrender.com`)

### Email Configuration (Required for user registration)
- `EMAIL_HOST_USER` - Your email address (e.g., Gmail)
- `EMAIL_HOST_PASSWORD` - Your email app password
- `DEFAULT_FROM_EMAIL` - Default from email (e.g., `Mansa <noreply@yourdomain.com>`)

### Supabase (if using)
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `SUPABASE_DB_URL` - Supabase database connection string

### Optional
- `DJANGO_DEBUG` - Set to `false` for production (default: false)
- `SENTRY_DSN` - Sentry DSN for error tracking
- `SENTRY_ENVIRONMENT` - Environment name (e.g., `production`)
- `THROTTLE_RATE_ANON` - Anonymous user rate limit (default: `50/min`)
- `THROTTLE_RATE_USER` - Authenticated user rate limit (default: `200/min`)

## Common Issues

### Database Connection Error
**Error**: `django.db.utils.OperationalError: [Errno -2] Name or service not known`

**Solution**:
- Ensure `DATABASE_URL` is set correctly in Render environment variables
- If using Render PostgreSQL, use the "Internal Database URL" (not External)
- Format should be: `postgresql://user:password@host:5432/dbname`

### Port Binding Error
**Error**: `No open ports detected`

**Solution**:
- Ensure you're using the provided gunicorn configuration (already configured to use PORT env var)
- The start command should be: `gunicorn config.wsgi:application -c gunicorn.conf.py`

### Static Files Not Loading
**Solution**:
- The build script runs `collectstatic` automatically
- Ensure `build.sh` is executable: `chmod +x build.sh`

## Quick Start

1. Create a new Web Service in Render
2. Connect your GitHub repository
3. Set Build Command: `./build.sh`
4. Set Start Command: `gunicorn config.wsgi:application -c gunicorn.conf.py`
5. Add a PostgreSQL database (or use external)
6. Set all required environment variables
7. Deploy!

## Verifying Deployment

After deployment, check:
1. Logs show `Booting worker` messages from gunicorn
2. No database connection errors
3. Service is listening on the assigned PORT
4. Health check endpoint responds (if configured)
