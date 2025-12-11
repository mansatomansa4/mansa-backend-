
# New Dashboard Features & API Endpoints

## Overview

Your dashboard now has **complete control** over all Supabase data with powerful new features:

✅ **Bulk Operations** - Update multiple items at once
✅ **Data Export** - Download CSV files for projects, applications, and members
✅ **Advanced Analytics** - Detailed statistics and metrics
✅ **Email Notifications** - Send emails directly to applicants from dashboard

---

## 🚀 New API Endpoints

### Projects

#### Bulk Update Projects
Update multiple projects at once (change status, priority, etc.)

```http
POST /api/platform/projects/bulk-update/
Authorization: Bearer <admin-token>  # REQUIRED
Content-Type: application/json

{
  "project_ids": [1, 5, 8, 12],
  "update_data": {
    "status": "active",
    "priority": "high"
  }
}

Response:
{
  "detail": "Successfully updated 4 projects",
  "updated_count": 4
}
```

**Use Cases**:
- Activate multiple draft projects at once
- Change priority for multiple projects
- Mark multiple projects as closed
- Update any field across multiple projects

---

#### Export Projects to CSV
Download all projects (or filtered subset) as CSV file

```http
GET /api/platform/projects/export/
Authorization: Bearer <token>  # Optional

Query Parameters:
- status: Filter by status (e.g., ?status=active)
- project_type: Filter by type
- priority: Filter by priority
- search: Search in title, description, objectives, deliverables

Response: CSV file download
Filename: projects_export_20240115_143022.csv

CSV Columns:
ID, Title, Description, Status, Location, Launch Date, Project Type,
Participants Count, Max Participants, Objectives, Deliverables,
Focal Person Name, Focal Person Email, Priority, Human Skills Required,
Platform Requirements, Timeline Start, Timeline End, Budget Estimate,
Current Budget, Is Concurrent, Created At
```

**Dashboard Button Example**:
```javascript
// Export all active projects
const exportProjects = async () => {
  const response = await fetch(
    `${API_BASE_URL}/platform/projects/export/?status=active`,
    { headers: getHeaders() }
  );
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'projects_export.csv';
  a.click();
};
```

---

#### Project Analytics
Get detailed analytics and statistics about all projects

```http
GET /api/platform/projects/analytics/
Authorization: Bearer <token>  # Optional

Response:
{
  "total_projects": 18,
  "by_status": {
    "active": 10,
    "draft": 3,
    "closed": 4,
    "completed": 1
  },
  "by_type": {
    "research": 5,
    "community": 8,
    "business": 3,
    "education": 2
  },
  "by_priority": {
    "high": 6,
    "medium": 8,
    "low": 3,
    "critical": 1
  },
  "total_participants": 245,
  "avg_participants": 13.6,
  "total_budget_estimate": 850000.00,
  "total_current_budget": 620000.00,
  "concurrent_projects": 5
}
```

**Perfect for Dashboard Charts**:
- Pie chart of projects by status
- Bar chart of budget allocation
- Donut chart of project types
- Priority distribution

---

### Applications

#### Bulk Approve Applications
Approve multiple applications at once

```http
POST /api/platform/applications/bulk-approve/
Authorization: Bearer <admin-token>  # REQUIRED
Content-Type: application/json

{
  "application_ids": [
    "123e4567-e89b-12d3-a456-426614174001",
    "123e4567-e89b-12d3-a456-426614174002",
    "123e4567-e89b-12d3-a456-426614174003"
  ],
  "reviewer_notes": "All applicants meet requirements - approved in bulk"
}

Response:
{
  "detail": "Successfully approved 3 applications",
  "updated_count": 3
}
```

---

#### Bulk Reject Applications
Reject multiple applications at once

```http
POST /api/platform/applications/bulk-reject/
Authorization: Bearer <admin-token>  # REQUIRED
Content-Type: application/json

{
  "application_ids": [
    "123e4567-e89b-12d3-a456-426614174004",
    "123e4567-e89b-12d3-a456-426614174005"
  ],
  "reviewer_notes": "Project capacity reached"
}

Response:
{
  "detail": "Successfully rejected 2 applications",
  "updated_count": 2
}
```

**Dashboard UI Example**:
```javascript
// Select checkboxes for multiple applications
const selectedIds = ['uuid1', 'uuid2', 'uuid3'];

// Bulk approve button
const bulkApprove = async () => {
  await api.post('/platform/applications/bulk-approve/', {
    application_ids: selectedIds,
    reviewer_notes: 'Bulk approved'
  });
  // Refresh application list
};
```

---

#### Export Applications to CSV
Download applications data as CSV

```http
GET /api/platform/applications/export/
Authorization: Bearer <token>  # Optional

Query Parameters:
- project_id: Filter by project
- status: Filter by status
- search: Search in name, email, skills, motivation

Response: CSV file download
Filename: applications_export_20240115_143530.csv

CSV Columns:
ID, Project ID, Applicant Name, Applicant Email, Skills, Motivation,
Status, Applied Date, Reviewed Date, Reviewer Notes, Created At
```

---

#### Application Analytics
Get statistics about applications

```http
GET /api/platform/applications/analytics/
Authorization: Bearer <token>  # Optional

Response:
{
  "total_applications": 40,
  "by_status": {
    "pending": 15,
    "approved": 20,
    "rejected": 5
  },
  "by_project": {
    "5": 9,   // Project ID: application count
    "12": 7,
    "8": 6,
    // ... more projects
  },
  "pending_count": 15,
  "approved_count": 20,
  "rejected_count": 5
}
```

---

#### Send Email to Applicant
Send custom email to a specific applicant from dashboard

```http
POST /api/platform/applications/{application_id}/send-email/
Authorization: Bearer <admin-token>  # REQUIRED
Content-Type: application/json

{
  "subject": "Additional Information Required",
  "message": "Dear Applicant,\n\nWe would like to request more information about your experience with Python..."
}

Response:
{
  "detail": "Email queued for sending"
}
```

**Use Cases**:
- Request additional information
- Send custom approval/rejection messages
- Notify about interview schedules
- Send project updates to approved applicants

---

### Members

#### Export Members to CSV
Download member data as CSV

```http
GET /api/platform/members/export/
# No authentication required

Query Parameters:
- country: Filter by country
- city: Filter by city
- membershiptype: Filter by membership type
- gender: Filter by gender
- is_active: Filter active members (true/false)
- search: Search in name, email, skills, expertise, occupation

Response: CSV file download
Filename: members_export_20240115_144015.csv

CSV Columns:
ID, Name, Email, Phone, Country, City, LinkedIn, Experience,
Area of Expertise, School, Level, Occupation, Job Title, Industry,
Major, Gender, Membership Type, Skills, Is Active, Created At
```

---

#### Member Analytics
Get detailed member statistics

```http
GET /api/platform/members/analytics/
# No authentication required

Response:
{
  "total_members": 350,
  "active_members": 320,
  "by_country": {
    "Sudan": 280,
    "Egypt": 30,
    "Saudi Arabia": 20,
    // Top 10 countries
  },
  "by_city": {
    "Khartoum": 150,
    "Omdurman": 80,
    "Khartoum North": 50,
    // Top 10 cities
  },
  "by_membership_type": {
    "Professional": 200,
    "Student": 120,
    "Academic": 30
  },
  "by_gender": {
    "Male": 220,
    "Female": 130
  },
  "by_experience": {
    "0-2 years": 100,
    "3-5 years": 150,
    "5+ years": 100
  },
  "by_industry": {
    "Technology": 180,
    "Education": 70,
    "Healthcare": 40,
    // Top 10 industries
  }
}
```

---

## 📊 Dashboard UI Implementation Guide

### 1. Enhanced Project Management

#### Create/Edit Project Form
Include ALL metadata fields in your dashboard form:

```javascript
const ProjectForm = () => {
  const [formData, setFormData] = useState({
    // Basic fields
    title: '',
    description: '',
    status: 'draft',
    location: '',
    launch_date: '',
    project_type: '',
    max_participants: 0,

    // Enhanced metadata fields
    objectives: '',
    deliverables: '',
    focal_person_name: '',
    focal_person_email: '',
    domain_tags: [],
    priority: 'medium',
    resources_needed: {},
    human_skills_required: '',
    platform_requirements: '',
    devices_required: '',
    timeline_start: '',
    timeline_end: '',
    budget_estimate: '',
    current_budget: '',
    is_concurrent: false,
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    await api.post('/platform/projects/', formData);
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Basic Information Section */}
      <section>
        <h3>Basic Information</h3>
        <input name="title" placeholder="Project Title" required />
        <textarea name="description" placeholder="Description" />
        <select name="status">
          <option value="draft">Draft</option>
          <option value="active">Active</option>
          <option value="closed">Closed</option>
        </select>
        <select name="priority">
          <option value="low">Low Priority</option>
          <option value="medium">Medium Priority</option>
          <option value="high">High Priority</option>
          <option value="critical">Critical</option>
        </select>
      </section>

      {/* Project Details Section */}
      <section>
        <h3>Project Details</h3>
        <textarea name="objectives" placeholder="Project Objectives" />
        <textarea name="deliverables" placeholder="Expected Deliverables" />
        <input name="focal_person_name" placeholder="Focal Person Name" />
        <input name="focal_person_email" type="email" placeholder="Focal Person Email" />
      </section>

      {/* Resources Section */}
      <section>
        <h3>Resources & Requirements</h3>
        <textarea name="human_skills_required" placeholder="Required Skills (e.g., Python, ML, Design)" />
        <textarea name="platform_requirements" placeholder="Platform Requirements" />
        <textarea name="devices_required" placeholder="Required Devices" />
      </section>

      {/* Timeline & Budget Section */}
      <section>
        <h3>Timeline & Budget</h3>
        <input name="timeline_start" type="date" placeholder="Start Date" />
        <input name="timeline_end" type="date" placeholder="End Date" />
        <input name="budget_estimate" type="number" placeholder="Budget Estimate" />
        <input name="current_budget" type="number" placeholder="Current Budget" />
      </section>

      {/* Tags & Flags */}
      <section>
        <label>
          <input type="checkbox" name="is_concurrent" />
          Can run concurrently with other projects
        </label>
      </section>

      <button type="submit">Create Project</button>
    </form>
  );
};
```

---

### 2. Bulk Operations UI

#### Select Multiple Items
```javascript
const ApplicationsList = () => {
  const [applications, setApplications] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);

  const toggleSelect = (id) => {
    setSelectedIds(prev =>
      prev.includes(id)
        ? prev.filter(i => i !== id)
        : [...prev, id]
    );
  };

  const bulkApprove = async () => {
    await api.post('/platform/applications/bulk-approve/', {
      application_ids: selectedIds,
      reviewer_notes: 'Bulk approved by admin'
    });
    // Refresh list
    fetchApplications();
    setSelectedIds([]);
  };

  return (
    <div>
      <div className="bulk-actions">
        <button onClick={bulkApprove} disabled={selectedIds.length === 0}>
          Approve Selected ({selectedIds.length})
        </button>
        <button onClick={bulkReject} disabled={selectedIds.length === 0}>
          Reject Selected ({selectedIds.length})
        </button>
      </div>

      <table>
        {applications.map(app => (
          <tr key={app.id}>
            <td>
              <input
                type="checkbox"
                checked={selectedIds.includes(app.id)}
                onChange={() => toggleSelect(app.id)}
              />
            </td>
            <td>{app.applicant_name}</td>
            <td>{app.status}</td>
          </tr>
        ))}
      </table>
    </div>
  );
};
```

---

### 3. Export Functionality

#### Export Button Component
```javascript
const ExportButton = ({ type, filters }) => {
  const handleExport = async () => {
    const queryString = new URLSearchParams(filters).toString();
    const url = `${API_BASE_URL}/platform/${type}/export/?${queryString}`;

    const response = await fetch(url, {
      headers: getHeaders()
    });

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = `${type}_export.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(downloadUrl);
  };

  return (
    <button onClick={handleExport} className="export-btn">
      📥 Export to CSV
    </button>
  );
};

// Usage
<ExportButton type="projects" filters={{ status: 'active' }} />
<ExportButton type="applications" filters={{ project_id: 5 }} />
<ExportButton type="members" filters={{ country: 'Sudan' }} />
```

---

### 4. Analytics Dashboard

#### Analytics Cards Component
```javascript
const AnalyticsDashboard = () => {
  const [projectAnalytics, setProjectAnalytics] = useState(null);
  const [appAnalytics, setAppAnalytics] = useState(null);
  const [memberAnalytics, setMemberAnalytics] = useState(null);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    const [projects, apps, members] = await Promise.all([
      api.get('/platform/projects/analytics/'),
      api.get('/platform/applications/analytics/'),
      api.get('/platform/members/analytics/')
    ]);
    setProjectAnalytics(projects.data);
    setAppAnalytics(apps.data);
    setMemberAnalytics(members.data);
  };

  return (
    <div className="analytics-dashboard">
      {/* Overview Cards */}
      <div className="cards-grid">
        <Card title="Total Projects" value={projectAnalytics?.total_projects} />
        <Card title="Total Budget" value={`$${projectAnalytics?.total_current_budget}`} />
        <Card title="Total Applications" value={appAnalytics?.total_applications} />
        <Card title="Total Members" value={memberAnalytics?.total_members} />
      </div>

      {/* Charts */}
      <div className="charts-grid">
        <PieChart
          title="Projects by Status"
          data={projectAnalytics?.by_status}
        />
        <BarChart
          title="Applications by Project"
          data={appAnalytics?.by_project}
        />
        <DonutChart
          title="Members by Country"
          data={memberAnalytics?.by_country}
        />
      </div>
    </div>
  );
};
```

---

### 5. Email Sending Interface

#### Send Email to Applicant Modal
```javascript
const SendEmailModal = ({ application, onClose }) => {
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');

  const handleSend = async () => {
    await api.post(`/platform/applications/${application.id}/send-email/`, {
      subject,
      message
    });
    alert('Email sent successfully!');
    onClose();
  };

  return (
    <Modal>
      <h3>Send Email to {application.applicant_name}</h3>
      <input
        type="text"
        placeholder="Subject"
        value={subject}
        onChange={(e) => setSubject(e.target.value)}
      />
      <textarea
        placeholder="Message"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        rows={10}
      />
      <button onClick={handleSend}>Send Email</button>
      <button onClick={onClose}>Cancel</button>
    </Modal>
  );
};
```

---

## 🎨 Complete Dashboard Features

### Project Management Page
- ✅ **List all projects** with filtering and search
- ✅ **Create new projects** with full metadata form
- ✅ **Edit existing projects** - all 40+ fields
- ✅ **Delete projects** with confirmation
- ✅ **Bulk update** multiple projects (status, priority, etc.)
- ✅ **Export filtered projects** to CSV
- ✅ **View project analytics** - charts and stats
- ✅ **Filter by**: status, type, priority
- ✅ **Search by**: title, description, objectives, deliverables

### Application Management Page
- ✅ **View all applications** with project details
- ✅ **Approve/reject** individual applications
- ✅ **Bulk approve** multiple applications
- ✅ **Bulk reject** multiple applications
- ✅ **Send custom emails** to applicants
- ✅ **Export applications** to CSV
- ✅ **View analytics** - by status, by project
- ✅ **Filter by**: project, status
- ✅ **Search by**: name, email, skills, motivation

### Member Management Page
- ✅ **List all members** from main website
- ✅ **View member profiles** - full details
- ✅ **Export members** to CSV
- ✅ **View member analytics** - by country, city, industry, etc.
- ✅ **Filter by**: country, city, membership type, gender
- ✅ **Search by**: name, email, skills, occupation

### Email Campaign Page
- ✅ **Create email templates** with variables
- ✅ **Send bulk campaigns** to targeted users
- ✅ **Send custom emails** to individual applicants
- ✅ **Track email delivery** status
- ✅ **View email logs** - sent, failed, opened

### Analytics Dashboard
- ✅ **Overview metrics** - totals and counts
- ✅ **Project analytics** - by status, type, priority, budget
- ✅ **Application analytics** - by status, by project
- ✅ **Member analytics** - demographics, industries, locations
- ✅ **Email metrics** - campaigns, delivery status
- ✅ **Visual charts** - pie, bar, donut, line charts
- ✅ **Export capabilities** - CSV for all data types

---

## 🔐 Security & Permissions

All new endpoints respect existing permission system:

- **Public** (AllowAny): List, view, export (filtered data)
- **Admin** (IsAdmin): Create, update, delete, bulk operations, email sending
- **Database Guard**: All endpoints return 503 in SQLite mode (requires PostgreSQL)

---

## 📝 Summary of Enhancements

### Projects
- Added `bulk-update` endpoint for mass updates
- Added `export` endpoint for CSV downloads
- Added `analytics` endpoint for statistics
- Enhanced search to include objectives and deliverables
- Added priority field filtering

### Applications
- Added `bulk-approve` endpoint
- Added `bulk-reject` endpoint
- Added `export` endpoint for CSV downloads
- Added `analytics` endpoint for statistics
- Added `send-email` endpoint for custom notifications
- Enhanced search to include skills and motivation

### Members
- Added `export` endpoint for CSV downloads
- Added `analytics` endpoint for demographics
- Added filtering by country, city, membership type, gender
- Enhanced search to include expertise and occupation

### Email System
- Created Celery tasks for sending emails to applicants
- Supports custom subject and message
- Professional HTML email templates
- Asynchronous sending (won't block dashboard)

---

## 🚀 Getting Started

1. **Backend is ready** - All endpoints are implemented
2. **Update your dashboard** - Use the code examples above
3. **Test the endpoints** - Use Swagger UI at `/api/docs/`
4. **Deploy** - Push changes and deploy

Your dashboard now has **complete administrative control** over all Supabase data! 🎉
