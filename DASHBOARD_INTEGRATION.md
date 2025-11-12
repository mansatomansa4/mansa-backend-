# Dashboard Integration Guide

## Overview

This guide explains how the Mansa Dashboard (`Mansa-dashboard`) integrates with the Mansa Backend (`mansa-backend`) and how to ensure they work together seamlessly.

## Architecture

- **Backend**: Django REST Framework API (this project) - Port 8000 (dev) / Deployed on Render
- **Dashboard**: Next.js 14 Admin Dashboard - Port 4000 (dev) / Can be deployed on Vercel
- **Database**: PostgreSQL (Supabase) - Shared between backend and dashboard
- **Authentication**: JWT tokens (Simple JWT)

## Backend API Endpoints

### Authentication Endpoints
- `POST /api/users/register/` - User registration
- `POST /api/users/token/` - Login (obtain JWT tokens)
- `POST /api/users/token/refresh/` - Refresh access token
- `GET /api/users/me/` - Get current authenticated user

### Admin User Management
- `GET /api/users/admin/users/` - List all users (Admin only)
- `GET /api/users/admin/users/pending/` - Get pending approval users
- `POST /api/users/admin/users/{id}/approve/` - Approve user
- `POST /api/users/admin/users/{id}/deny/` - Deny user
- `PATCH /api/users/admin/users/{id}/` - Update user
- `DELETE /api/users/admin/users/{id}/` - Delete user

### Platform Data (Supabase)
These endpoints access Supabase data (Members, Projects, Applications from the main platform):
- `GET /api/platform/members/` - List platform members
- `GET /api/platform/members/verify/?email=<email>` - Verify member email
- `GET /api/platform/projects/` - List Supabase projects
- `GET /api/platform/applications/` - List Supabase applications
- `GET /api/platform/applications/check/?project_id=<id>&email=<email>` - Check existing application

**Note**: Platform endpoints return 503 when using SQLite (local dev). They require PostgreSQL/Supabase connection.

### Project Management (Django)
- `GET /api/projects/` - List projects
- `POST /api/projects/` - Create project (Admin only)
- `GET /api/projects/{id}/` - Get project details
- `PATCH /api/projects/{id}/` - Update project (Admin only)
- `DELETE /api/projects/{id}/` - Delete project (Admin only)
- `POST /api/projects/{id}/approve/` - Approve project (Admin only)
- `POST /api/projects/{id}/deny/` - Deny project (Admin only)

### Application Management
- `GET /api/applications/` - List all applications (Admin only)
- `GET /api/applications/{id}/` - Get application details (Admin only)
- `POST /api/applications/{id}/approve/` - Approve application (Admin only)
- `POST /api/applications/{id}/deny/` - Deny application (Admin only)
- `DELETE /api/applications/{id}/` - Delete application (Admin only)

### Email Management
- `GET /api/emails/templates/` - List email templates (Admin only)
- `POST /api/emails/templates/` - Create email template (Admin only)
- `PATCH /api/emails/templates/{id}/` - Update template (Admin only)
- `DELETE /api/emails/templates/{id}/` - Delete template (Admin only)
- `GET /api/emails/campaigns/` - List campaigns (Admin only)
- `POST /api/emails/campaigns/` - Create campaign (Admin only)
- `POST /api/emails/campaigns/{id}/send/` - Send campaign (Admin only)
- `GET /api/emails/logs/` - View email logs (Admin only)

### Analytics
- `GET /api/admin/analytics/overview/` - Overview metrics (Admin only)
- `GET /api/admin/analytics/users/` - User analytics (Admin only)
- `GET /api/admin/analytics/projects/` - Project analytics (Admin only)
- `GET /api/admin/analytics/emails/` - Email analytics (Admin only)

## CORS Configuration

### Development
The backend is pre-configured to allow requests from:
- `http://localhost:3000` (Main frontend)
- `http://127.0.0.1:3000`
- `http://localhost:4000` (Admin dashboard)
- `http://127.0.0.1:4000`

### Production
To add production dashboard URLs, update the `.env` file:

```bash
# In mansa-backend/.env
CORS_ALLOWED_ORIGINS=https://dashboard.yourdomain.com,https://admin.yourdomain.com
```

The backend will automatically add these to the allowed origins list.

## Dashboard Configuration

### Environment Variables

The dashboard requires the following environment variables in `.env.local`:

```bash
# Backend API URL
NEXT_PUBLIC_API_BASE_URL=https://mansa-backend-1rr8.onrender.com/api

# Email Configuration (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

### Local Development

For local development, change the API URL:

```bash
# In Mansa-dashboard/.env.local
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api
```

## Authentication Flow

1. **Login**:
   - Dashboard sends credentials to `POST /api/users/token/`
   - Backend validates and returns access + refresh tokens
   - Dashboard stores tokens in localStorage
   - Dashboard verifies user role is `admin` or `super_admin`

2. **API Requests**:
   - Dashboard includes `Authorization: Bearer <access_token>` header
   - Backend validates JWT token
   - Backend checks user permissions

3. **Token Refresh**:
   - When access token expires (60 minutes), dashboard automatically calls `POST /api/users/token/refresh/`
   - New access token is returned and stored
   - Request is retried with new token

4. **Logout**:
   - Dashboard clears tokens from localStorage
   - Redirects to login page

## Running Both Services

### Backend (Port 8000)
```bash
cd mansa-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Dashboard (Port 4000)
```bash
cd Mansa-dashboard
npm install
npm run dev -- -p 4000
```

Visit:
- Backend API: http://127.0.0.1:8000/api/
- API Docs: http://127.0.0.1:8000/api/docs/
- Dashboard: http://localhost:4000

## Database Setup

### Supabase Configuration

The backend connects to Supabase PostgreSQL. Update `.env`:

```bash
# Supabase credentials
SUPABASE_URL=https://your-instance.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Database URL (Supabase Transaction Pooler)
DATABASE_URL=postgresql://postgres.your-instance:password@host:6543/postgres
```

### Schema

The backend manages:
- Django users (admin accounts)
- Projects created through admin dashboard
- Project applications
- Email templates, campaigns, and logs

Supabase manages:
- Platform members (registered on main site)
- Platform projects (created on main site)
- Platform applications (submitted on main site)

## Deployment

### Backend (Render)
Already deployed at: https://mansa-backend-1rr8.onrender.com

Environment variables to set on Render:
- `DJANGO_SECRET_KEY` - Random secret key
- `DJANGO_DEBUG=false`
- `DJANGO_ALLOWED_HOSTS` - Your domain
- `DATABASE_URL` - Supabase connection string
- `CORS_ALLOWED_ORIGINS` - Dashboard URLs (comma-separated)
- `EMAIL_HOST_USER` - SMTP username
- `EMAIL_HOST_PASSWORD` - SMTP password

### Dashboard (Vercel)
1. Push dashboard code to GitHub
2. Connect repository to Vercel
3. Set environment variables:
   - `NEXT_PUBLIC_API_BASE_URL=https://mansa-backend-1rr8.onrender.com/api`
   - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`
   - `DEFAULT_FROM_EMAIL`
4. Deploy

After deployment, add dashboard URL to backend CORS:
```bash
# In Render environment variables
CORS_ALLOWED_ORIGINS=https://your-dashboard.vercel.app
```

## Testing the Integration

### 1. Test Authentication
```bash
# Login
curl -X POST http://127.0.0.1:8000/api/users/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "password"}'

# Response includes access and refresh tokens
```

### 2. Test Protected Endpoint
```bash
# Get current user
curl -X GET http://127.0.0.1:8000/api/users/me/ \
  -H "Authorization: Bearer <access_token>"
```

### 3. Test Dashboard Connection
1. Start backend: `python manage.py runserver`
2. Start dashboard: `npm run dev -- -p 4000`
3. Open dashboard: http://localhost:4000
4. Login with admin credentials
5. Verify all pages load without CORS errors

## Common Issues

### CORS Errors
**Problem**: Dashboard can't connect to backend, CORS errors in console

**Solution**:
- Check `CORS_ALLOWED_ORIGINS` in backend `.env`
- Ensure dashboard URL is included
- Restart backend after changing CORS settings

### Authentication Fails
**Problem**: Login works but subsequent requests fail with 401

**Solution**:
- Check token expiration (default 60 minutes)
- Verify `Authorization` header format: `Bearer <token>`
- Check user role is `admin` or `super_admin`

### Platform Data Unavailable (503 Error)
**Problem**: Members/Platform Projects show "unavailable in sqlite mode"

**Solution**:
- Configure PostgreSQL/Supabase connection
- Update `DATABASE_URL` in `.env`
- These endpoints require PostgreSQL, not SQLite

### Email Not Sending
**Problem**: Email functionality uses mailto fallback

**Solution**:
- Configure SMTP settings in dashboard `.env.local`
- For Gmail, use App Password, not regular password
- Verify SMTP credentials are correct

## API Client (Dashboard)

The dashboard uses a centralized API client located at `src/lib/api.ts`:

```typescript
import { apiClient } from '@/lib/api';

// Login
const { access, refresh } = await apiClient.login(email, password);

// Get current user
const user = await apiClient.getMe();

// List users (admin)
const users = await apiClient.getUsers();
```

The client handles:
- Automatic token refresh
- Error handling
- Type safety (TypeScript)
- Authorization headers

## Security Considerations

1. **JWT Tokens**: Stored in localStorage (consider httpOnly cookies for production)
2. **CORS**: Only allow trusted dashboard domains
3. **HTTPS**: Always use HTTPS in production
4. **API Keys**: Keep Supabase keys in environment variables
5. **Email Credentials**: Use app passwords, not account passwords

## Support

For issues:
- Backend issues: Check Django logs and `python manage.py runserver` output
- Dashboard issues: Check browser console and Next.js dev server output
- Database issues: Check Supabase dashboard logs

## Next Steps

1. Deploy dashboard to Vercel/Netlify
2. Add production dashboard URL to backend CORS
3. Set up automated backups for database
4. Configure monitoring (Sentry for both services)
5. Set up CI/CD pipelines
