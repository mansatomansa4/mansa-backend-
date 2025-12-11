# Dashboard API Reference

## Architecture Overview

```
Dashboard (Next.js) → Backend API (Django) → Supabase Database
```

**Important**: The dashboard ONLY communicates with the backend API. The backend handles all Supabase operations. This provides:
- Centralized authentication and authorization
- Data validation and business logic
- Security and access control
- Consistent API interface

---

## Authentication

### Login
```http
POST /api/users/token/
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "your-password"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Refresh Token
```http
POST /api/users/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Use Access Token
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

## Project Management (Supabase)

All project endpoints require admin authentication except LIST and RETRIEVE (public).

### List All Projects
```http
GET /api/platform/projects/
Authorization: Bearer <token>  # Optional for viewing

Query Parameters:
- status (exact/in): Filter by status (e.g., ?status=active)
- project_type (exact/in): Filter by type
- search: Search in title and description
- ordering: Sort by fields (e.g., ?ordering=-created_at)

Response:
[
  {
    "id": 1,
    "title": "AI Research Initiative",
    "description": "Research project focused on AI",
    "status": "active",
    "location": "Khartoum, Sudan",
    "launch_date": "2024-01-15",
    "image_url": "https://adnteftmqytcnieqmlma.supabase.co/storage/v1/object/public/project-images/ai-research.jpg",
    "project_type": "research",
    "tags": ["AI", "Machine Learning"],
    "participants_count": 15,
    "max_participants": 20,
    "member_id": "550e8400-e29b-41d4-a716-446655440000",

    // Enhanced Metadata Fields
    "objectives": "Advance AI research in Sudan",
    "deliverables": "Research papers, ML models",
    "focal_person_id": "550e8400-e29b-41d4-a716-446655440001",
    "focal_person_name": "Dr. Ahmed Ali",
    "focal_person_email": "ahmed@example.com",
    "domain_tags": ["AI", "ML", "Research"],
    "priority": "high",
    "resources_needed": {
      "budget": 50000,
      "equipment": ["GPUs", "Servers"],
      "software": ["TensorFlow", "PyTorch"]
    },
    "human_skills_required": "Python, Machine Learning, Data Science",
    "platform_requirements": "Cloud computing (AWS/GCP)",
    "devices_required": "High-performance GPUs",
    "timeline_start": "2024-01-01",
    "timeline_end": "2024-12-31",
    "budget_estimate": "50000.00",
    "current_budget": "35000.00",
    "is_concurrent": true,

    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-15T14:30:00Z"
  }
]
```

### Get Single Project
```http
GET /api/platform/projects/{id}/
Authorization: Bearer <token>  # Optional for viewing

Response: Same structure as list item
```

### Create Project
```http
POST /api/platform/projects/
Authorization: Bearer <admin-token>  # REQUIRED
Content-Type: application/json

{
  "title": "New Project",
  "description": "Project description",
  "status": "draft",  // draft, active, closed, completed
  "location": "Khartoum, Sudan",
  "launch_date": "2024-06-01",
  "image_url": "path/to/image.jpg",  // Will be converted to full URL
  "project_type": "community",  // research, community, business, etc.
  "tags": ["Innovation", "Community"],
  "max_participants": 30,
  "member_id": "550e8400-e29b-41d4-a716-446655440000",

  // Enhanced metadata (all optional)
  "objectives": "Build community capacity",
  "deliverables": "Training materials, workshops",
  "focal_person_name": "Sarah Ahmed",
  "focal_person_email": "sarah@example.com",
  "domain_tags": ["Education", "Community"],
  "priority": "medium",  // low, medium, high, critical
  "resources_needed": {
    "budget": 20000,
    "venue": "Community center",
    "materials": ["Laptops", "Projector"]
  },
  "human_skills_required": "Teaching, Communication",
  "platform_requirements": "Basic internet",
  "devices_required": "Laptops, tablets",
  "timeline_start": "2024-06-01",
  "timeline_end": "2024-12-01",
  "budget_estimate": "20000.00",
  "current_budget": "0.00",
  "is_concurrent": false
}

Response: Created project object
```

### Update Project
```http
PATCH /api/platform/projects/{id}/
Authorization: Bearer <admin-token>  # REQUIRED
Content-Type: application/json

{
  "status": "active",
  "participants_count": 16,
  "current_budget": "40000.00"
  // Any fields you want to update
}

Response: Updated project object
```

### Delete Project
```http
DELETE /api/platform/projects/{id}/
Authorization: Bearer <admin-token>  # REQUIRED

Response: 204 No Content
```

---

## Application Management (Supabase)

### List All Applications
```http
GET /api/platform/applications/
Authorization: Bearer <token>  # Optional for viewing

Query Parameters:
- project_id: Filter by project (e.g., ?project_id=5)
- status: Filter by status (pending, approved, rejected)
- search: Search in applicant name and email

Response:
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "project_id": 5,
    "member_id": "550e8400-e29b-41d4-a716-446655440000",
    "applicant_name": "John Doe",
    "applicant_email": "john@example.com",
    "skills": "Python, Machine Learning",
    "motivation": "I'm passionate about AI research...",
    "status": "pending",  // pending, approved, rejected
    "applied_date": "2024-01-10T09:30:00Z",
    "reviewed_date": null,
    "reviewer_notes": "",
    "created_at": "2024-01-10T09:30:00Z",
    "updated_at": "2024-01-10T09:30:00Z"
  }
]
```

### Get Single Application
```http
GET /api/platform/applications/{id}/
Authorization: Bearer <token>  # Optional

Response: Same structure as list item
```

### Check Existing Application
```http
GET /api/platform/applications/check/?project_id=5&email=john@example.com
Authorization: Bearer <token>  # Optional

Response:
{
  "exists": true,
  "application": { /* application object */ }
}
// OR
{
  "exists": false
}
```

### Create Application (Public)
```http
POST /api/platform/applications/
Content-Type: application/json
# No authentication required

{
  "project_id": 5,
  "applicant_name": "Jane Smith",
  "applicant_email": "jane@example.com",
  "skills": "React, Node.js, MongoDB",
  "motivation": "I want to contribute to this project because...",
  "member_id": "550e8400-e29b-41d4-a716-446655440001"  // Optional
}

Response: Created application with status "pending"
```

### Update Application (Approve/Reject)
```http
PATCH /api/platform/applications/{id}/
Authorization: Bearer <admin-token>  # REQUIRED
Content-Type: application/json

{
  "status": "approved",  // approved or rejected
  "reviewer_notes": "Great skills, approved!",
  "reviewed_date": "2024-01-11T10:00:00Z"
}

Response: Updated application object
```

---

## Member Management (Supabase)

### List All Members
```http
GET /api/platform/members/
# No authentication required

Response:
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Ahmed Hassan",
    "email": "ahmed@example.com",
    "phone": "+249123456789",
    "country": "Sudan",
    "city": "Khartoum",
    "linkedin": "https://linkedin.com/in/ahmedhassan",
    "experience": "5 years",
    "areaOfExpertise": "Software Development",
    "school": "University of Khartoum",
    "level": "Senior",
    "occupation": "Software Engineer",
    "jobtitle": "Senior Developer",
    "industry": "Technology",
    "major": "Computer Science",
    "gender": "Male",
    "membershiptype": "Professional",
    "skills": "Python, JavaScript, Django",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### Verify Member Email
```http
GET /api/platform/members/verify/?email=ahmed@example.com
# No authentication required

Response:
{
  "exists": true,
  "member": { /* member object */ }
}
// OR
{
  "exists": false
}
```

### Register New Member
```http
POST /api/platform/members/
Content-Type: application/json
# No authentication required

{
  "name": "Sarah Ahmed",
  "email": "sarah@example.com",
  "phone": "+249987654321",
  "country": "Sudan",
  "city": "Omdurman",
  "gender": "Female",
  "membershiptype": "Student",
  "skills": "Design, UX/UI",
  "experience": "2 years",
  "areaOfExpertise": "Product Design",
  // ... other optional fields
}

Response: Created member object
```

---

## Community Members (Supabase)

### List Community Members
```http
GET /api/platform/community-members/
Authorization: Bearer <token>  # REQUIRED (authenticated users)

Response:
[
  {
    "id": "650e8400-e29b-41d4-a716-446655440000",
    "name": "Community Member",
    "email": "member@example.com",
    "phone": "+249111222333",
    "joined_date": "2024-01-01T00:00:00Z",
    "is_active": true,
    "profile_picture": "path/to/picture.jpg",
    "bio": "Passionate about community development",
    "location": "Khartoum",
    "skills": "Community organizing",
    "motivation": "Want to make a difference",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

---

## Email Management

All email endpoints require admin authentication.

### List Email Templates
```http
GET /api/emails/templates/
Authorization: Bearer <admin-token>  # REQUIRED

Response:
[
  {
    "id": 1,
    "name": "Welcome Email",
    "template_type": "welcome",  // welcome, approval, denial, campaign, notification
    "subject": "Welcome to Mansa, {name}!",
    "html_content": "<html>...</html>",
    "text_content": "Welcome to Mansa...",
    "is_active": true,
    "created_by": 1,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### Create Email Template
```http
POST /api/emails/templates/
Authorization: Bearer <admin-token>  # REQUIRED
Content-Type: application/json

{
  "name": "Project Approval",
  "template_type": "notification",
  "subject": "Your application has been approved!",
  "html_content": "<html><body><p>Dear {name},</p><p>Congratulations! Your application for {project} has been approved.</p></body></html>",
  "text_content": "Dear {name}, Congratulations! Your application for {project} has been approved.",
  "is_active": true
}

Response: Created template object
```

### Update Email Template
```http
PATCH /api/emails/templates/{id}/
Authorization: Bearer <admin-token>  # REQUIRED
Content-Type: application/json

{
  "subject": "Updated subject",
  "html_content": "<html>...</html>"
}

Response: Updated template object
```

### Delete Email Template
```http
DELETE /api/emails/templates/{id}/
Authorization: Bearer <admin-token>  # REQUIRED

Response: 204 No Content
```

---

## Email Campaigns

### List Email Campaigns
```http
GET /api/emails/campaigns/
Authorization: Bearer <admin-token>  # REQUIRED

Response:
[
  {
    "id": 1,
    "name": "Monthly Newsletter",
    "template": 2,  // Template ID
    "target_all_users": false,
    "target_approved_users": true,
    "target_pending_users": false,
    "specific_users": [1, 5, 10],  // User IDs
    "scheduled_at": "2024-02-01T10:00:00Z",
    "sent_at": null,
    "status": "scheduled",  // draft, scheduled, sending, sent, failed
    "created_by": 1,
    "created_at": "2024-01-25T00:00:00Z"
  }
]
```

### Create Email Campaign
```http
POST /api/emails/campaigns/
Authorization: Bearer <admin-token>  # REQUIRED
Content-Type: application/json

{
  "name": "Project Update Announcement",
  "template": 3,  // Template ID
  "target_all_users": true,
  "target_approved_users": false,
  "target_pending_users": false,
  "specific_users": [],
  "scheduled_at": "2024-02-15T09:00:00Z",
  "status": "draft"
}

Response: Created campaign object
```

### Send Email Campaign
```http
POST /api/emails/campaigns/{id}/send/
Authorization: Bearer <admin-token>  # REQUIRED

Response:
{
  "detail": "Campaign queued"
}
```

Campaign will be sent asynchronously via Celery. Status will change:
- draft/scheduled → sending → sent

### View Email Logs
```http
GET /api/emails/logs/
Authorization: Bearer <admin-token>  # REQUIRED

Response:
[
  {
    "id": 1,
    "recipient": 5,  // User ID
    "campaign": 1,  // Campaign ID (if part of campaign)
    "template": 2,  // Template ID
    "subject": "Welcome to Mansa!",
    "status": "sent",  // queued, sent, failed, bounced, opened, clicked
    "error_message": null,
    "sent_at": "2024-01-10T10:00:00Z",
    "opened_at": null,
    "clicked_at": null,
    "created_at": "2024-01-10T09:59:00Z"
  }
]
```

---

## User Management (Django Users)

### List All Users (Admin)
```http
GET /api/users/admin/users/
Authorization: Bearer <admin-token>  # REQUIRED

Response:
[
  {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user",  // user, admin, super_admin
    "approval_status": "approved",  // pending, approved, denied
    "phone_number": "+249123456789",
    "profile_picture": "/media/profiles/pic.jpg",
    "bio": "Software developer",
    "date_approved": "2024-01-05T10:00:00Z",
    "approved_by": 2,
    "is_active": true,
    "date_joined": "2024-01-01T00:00:00Z"
  }
]
```

### List Pending Users
```http
GET /api/users/admin/users/pending/
Authorization: Bearer <admin-token>  # REQUIRED

Response: List of users with approval_status="pending"
```

### Approve User
```http
POST /api/users/admin/users/{id}/approve/
Authorization: Bearer <admin-token>  # REQUIRED

Response: Updated user object with approval_status="approved"
# Also triggers approval email via Celery
```

### Deny User
```http
POST /api/users/admin/users/{id}/deny/
Authorization: Bearer <admin-token>  # REQUIRED

Response: Updated user object with approval_status="denied"
# Also triggers denial email via Celery
```

### Update User
```http
PATCH /api/users/admin/users/{id}/
Authorization: Bearer <admin-token>  # REQUIRED
Content-Type: application/json

{
  "role": "admin",
  "approval_status": "approved"
}

Response: Updated user object
```

### Delete User
```http
DELETE /api/users/admin/users/{id}/
Authorization: Bearer <admin-token>  # REQUIRED

Response: 204 No Content
```

---

## Analytics (Admin)

All analytics endpoints require admin authentication.

### Overview Metrics
```http
GET /api/admin/analytics/overview/
Authorization: Bearer <admin-token>  # REQUIRED

Response:
{
  "total_users": 150,
  "total_projects": 18,
  "total_applications": 40,
  "total_emails_24h": 25
}
```

### User Metrics
```http
GET /api/admin/analytics/users/
Authorization: Bearer <admin-token>  # REQUIRED

Response:
{
  "by_status": {
    "approved": 120,
    "pending": 25,
    "denied": 5
  },
  "by_role": {
    "user": 140,
    "admin": 8,
    "super_admin": 2
  }
}
```

### Project Metrics
```http
GET /api/admin/analytics/projects/
Authorization: Bearer <admin-token>  # REQUIRED

Response:
{
  "by_status": {
    "active": 10,
    "draft": 3,
    "closed": 4,
    "archived": 1
  },
  "by_approval": {
    "approved": 15,
    "pending": 2,
    "denied": 1
  }
}
```

### Email Metrics
```http
GET /api/admin/analytics/emails/
Authorization: Bearer <admin-token>  # REQUIRED

Response:
{
  "campaigns": {
    "total": 5,
    "sent": 3,
    "scheduled": 2
  },
  "logs": {
    "sent": 450,
    "failed": 12,
    "opened": 320
  }
}
```

---

## Health Check (Public)

### Check API Health
```http
GET /api/health/
# No authentication required

Response:
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:00:00Z"
}
```

---

## API Documentation

### OpenAPI Schema
```http
GET /api/schema/
# Download OpenAPI 3.0 schema
```

### Interactive Swagger UI
```
GET /api/docs/
# Opens interactive API documentation in browser
```

### ReDoc Documentation
```
GET /api/redoc/
# Opens beautiful API reference documentation
```

---

## Error Responses

All endpoints return standard error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid data",
  "field_errors": {
    "email": ["This field is required"]
  }
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 503 Service Unavailable (SQLite Mode)
```json
{
  "detail": "Remote data unavailable in sqlite mode"
}
```

---

## Rate Limiting

- **Anonymous requests**: 50/minute
- **Authenticated requests**: 200/minute

Rate limit exceeded response:
```json
{
  "detail": "Request was throttled. Expected available in 42 seconds."
}
```

---

## Image URLs

Image URLs are automatically converted from relative paths to full Supabase storage URLs:

**Input**: `path/to/image.jpg`
**Output**: `https://adnteftmqytcnieqmlma.supabase.co/storage/v1/object/public/project-images/path/to/image.jpg`

---

## Best Practices for Dashboard

1. **Token Management**:
   - Store access token in localStorage or memory
   - Refresh token before expiry (60 min lifetime)
   - Clear tokens on logout

2. **Error Handling**:
   - Handle 401 errors by refreshing token or redirecting to login
   - Show user-friendly error messages
   - Log errors for debugging

3. **Data Fetching**:
   - Use pagination for large lists
   - Implement debounced search
   - Cache responses when appropriate

4. **Optimistic Updates**:
   - Update UI immediately for better UX
   - Revert on error
   - Show loading states

5. **Security**:
   - Never expose admin tokens in client code
   - Validate all user input before sending
   - Use HTTPS in production

---

## Example Dashboard API Client (JavaScript)

```javascript
// api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

class DashboardAPI {
  private getHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
  }

  // Projects
  async getProjects(params = {}) {
    const query = new URLSearchParams(params).toString();
    const response = await fetch(`${API_BASE_URL}/platform/projects/?${query}`, {
      headers: this.getHeaders()
    });
    return response.json();
  }

  async createProject(data) {
    const response = await fetch(`${API_BASE_URL}/platform/projects/`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data)
    });
    return response.json();
  }

  async updateProject(id, data) {
    const response = await fetch(`${API_BASE_URL}/platform/projects/${id}/`, {
      method: 'PATCH',
      headers: this.getHeaders(),
      body: JSON.stringify(data)
    });
    return response.json();
  }

  async deleteProject(id) {
    await fetch(`${API_BASE_URL}/platform/projects/${id}/`, {
      method: 'DELETE',
      headers: this.getHeaders()
    });
  }

  // Applications
  async getApplications(projectId = null) {
    const query = projectId ? `?project_id=${projectId}` : '';
    const response = await fetch(`${API_BASE_URL}/platform/applications/${query}`, {
      headers: this.getHeaders()
    });
    return response.json();
  }

  async approveApplication(id) {
    const response = await fetch(`${API_BASE_URL}/platform/applications/${id}/`, {
      method: 'PATCH',
      headers: this.getHeaders(),
      body: JSON.stringify({
        status: 'approved',
        reviewed_date: new Date().toISOString()
      })
    });
    return response.json();
  }

  // Email Campaigns
  async sendCampaign(id) {
    const response = await fetch(`${API_BASE_URL}/emails/campaigns/${id}/send/`, {
      method: 'POST',
      headers: this.getHeaders()
    });
    return response.json();
  }
}

export const api = new DashboardAPI();
```

---

## Summary

Your dashboard has **full control** over:

✅ **Projects**: Create, read, update, delete with all metadata fields
✅ **Applications**: View, approve, reject
✅ **Members**: View, register, verify
✅ **Emails**: Templates, campaigns, bulk sending
✅ **Users**: Manage, approve, roles
✅ **Analytics**: Real-time metrics

All operations go through the secure backend API - no direct Supabase connection needed!
