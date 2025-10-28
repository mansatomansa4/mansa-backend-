# Mansa Backend Setup & Database Migration Instructions

## Prerequisites
- Access to Supabase dashboard
- PostgreSQL database credentials
- Python 3.9+ installed locally

## Step 1: Run Database Migrations on Supabase

### 1.1 Access Supabase SQL Editor
1. Log in to [Supabase Dashboard](https://app.supabase.com)
2. Select your project: `adnteftmqytcnieqmlma`
3. Navigate to **SQL Editor** in the left sidebar

### 1.2 Run Migration #1: Add Project Metadata Fields
1. Open the file: `migrations/001_add_project_metadata.sql`
2. Copy the entire SQL content
3. Paste into Supabase SQL Editor
4. Click **RUN** button
5. Verify success message appears

**What this does:**
- Adds 17 new columns to `projects` table
- Creates indexes for performance
- Adds foreign key for focal_person_id
- Creates trigger to sync focal person data

### 1.3 Run Migration #2: Seed Sample Projects
1. Open the file: `migrations/002_seed_sample_projects.sql`
2. Copy the entire SQL content
3. Paste into Supabase SQL Editor
4. Click **RUN** button
5. Verify 5 sample projects are inserted

**Sample Projects Included:**
1. Mansa AI Research Initiative (Future, High Priority)
2. CyberSecurity Training Platform (Future, Critical Priority)
3. Digital Health Records System (Ongoing, High Priority)
4. Agricultural AI Prediction System (Ongoing, High Priority)
5. Quantum Computing Research Lab (Future, Medium Priority)

### 1.4 Verify Data
Run this query in SQL Editor to verify:
```sql
SELECT id, title, domain_tags, priority, project_type, status
FROM public.projects
ORDER BY created_at DESC;
```

You should see 5 projects with all metadata populated.

---

## Step 2: Configure Backend Environment

### 2.1 Get Database Connection String from Supabase
1. In Supabase Dashboard, go to **Settings** → **Database**
2. Scroll to **Connection String** section
3. Select **URI** tab
4. Copy the connection string (it looks like):
   ```
   postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:5432/postgres
   ```

### 2.2 Update Local .env File
Edit `.env` file in backend root:

```env
# Update this line with your actual Supabase database URL
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-us-west-1.pooler.supabase.com:5432/postgres
```

**Important:** Replace `[PROJECT-REF]` and `[PASSWORD]` with your actual values

### 2.3 Update Render.com Environment Variables
1. Go to [Render.com Dashboard](https://dashboard.render.com)
2. Select your backend service: `mansa-backend`
3. Go to **Environment** tab
4. Add/Update the `DATABASE_URL` variable with the same connection string
5. Click **Save Changes**
6. Render will automatically redeploy

---

## Step 3: Test Backend Locally

### 3.1 Install Dependencies
```bash
cd mansa-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3.2 Run Development Server
```bash
python manage.py runserver
```

### 3.3 Test API Endpoints
Open a new terminal and run:

```bash
# Test health endpoint
curl http://localhost:8000/api/health/

# Test projects endpoint
curl http://localhost:8000/api/projects/

# Test with filters
curl "http://localhost:8000/api/projects/?project_type=future"
curl "http://localhost:8000/api/projects/?priority=high"
curl "http://localhost:8000/api/projects/?status=Active"
```

**Expected Response:**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Mansa AI Research Initiative",
      "description": "...",
      "objectives": "...",
      "deliverables": "...",
      "domain_tags": ["AI", "ML", "Research", "Ethics"],
      "priority": "high",
      "project_type": "future",
      ...
    }
  ]
}
```

---

## Step 4: Verify Production Backend

### 4.1 Wait for Render Deploy
After updating environment variables, wait 2-3 minutes for Render to redeploy.

### 4.2 Test Production Endpoints
```bash
# Test health
curl https://mansa-backend-1rr8.onrender.com/api/health/

# Test projects
curl https://mansa-backend-1rr8.onrender.com/api/projects/

# Test with domain tag filter
curl "https://mansa-backend-1rr8.onrender.com/api/projects/?domain_tags__contains=AI"
```

---

## Step 5: Update Frontend

The frontend has already been updated with the new API integration. Once the backend is working:

1. Start frontend dev server:
   ```bash
   cd mansa-to-mansa
   npm run dev
   ```

2. Visit: `http://localhost:3000/projects`

3. You should see:
   - Loading skeleton while fetching
   - Projects loaded from backend
   - All new metadata fields displayed

---

## Available API Endpoints

### GET /api/projects/
List all projects with pagination

**Query Parameters:**
- `project_type` - Filter by type: `ongoing` or `future`
- `status` - Filter by status: `Concept`, `Planning`, `Active`, `Completed`
- `priority` - Filter by priority: `low`, `medium`, `high`, `critical`
- `domain_tags__contains` - Filter by domain tag (e.g., `AI`, `CyberSecurity`)
- `search` - Search in title and description
- `ordering` - Sort by field (e.g., `-created_at`, `title`)

**Example Requests:**
```bash
# Get all future projects
GET /api/projects/?project_type=future

# Get high priority projects
GET /api/projects/?priority=high

# Get AI-related projects
GET /api/projects/?domain_tags__contains=AI

# Get ongoing projects sorted by title
GET /api/projects/?project_type=ongoing&ordering=title
```

### GET /api/projects/{id}/
Get single project by ID

**Example:**
```bash
GET /api/projects/1/
```

### GET /api/projects/{id}/applications/
Get all applications for a project (requires authentication)

### POST /api/projects/{id}/apply/
Submit application to join a project

---

## New Project Metadata Fields

### Core Metadata
- **objectives** - Project objectives and goals (TEXT)
- **deliverables** - Expected deliverables and outcomes (TEXT)

### Focal Person / Project Lead
- **focal_person_id** - UUID of project lead from members table
- **focal_person_name** - Cached name of focal person
- **focal_person_email** - Cached email of focal person

### Domain & Priority
- **domain_tags** - Array of domains (e.g., `["AI", "CyberSecurity", "BIOTECH"]`)
- **priority** - Priority level: `low`, `medium`, `high`, `critical`

### Resources
- **resources_needed** - JSON object with resource requirements
- **human_skills_required** - Skills needed for implementation (TEXT)
- **platform_requirements** - Platform/software requirements (TEXT)
- **devices_required** - Physical devices needed (TEXT)

### Timeline & Budget
- **timeline_start** - Project start date (DATE)
- **timeline_end** - Expected completion date (DATE)
- **budget_estimate** - Estimated budget (DECIMAL)
- **current_budget** - Current allocated/spent budget (DECIMAL)

### Concurrent Execution
- **is_concurrent** - Whether project can run concurrently (BOOLEAN)

---

## Troubleshooting

### Issue: Backend still returns 500 errors
**Solution:**
1. Verify DATABASE_URL is correctly set on Render
2. Check Render logs for specific error messages
3. Ensure migrations were run successfully on Supabase
4. Restart the Render service manually

### Issue: No data returned from API
**Solution:**
1. Verify sample data was inserted by running the seed SQL
2. Check database connection in Supabase
3. Ensure tables have correct permissions

### Issue: Frontend shows "Failed to load projects"
**Solution:**
1. Check browser console for errors
2. Verify backend URL is correct in `src/lib/api.ts`
3. Test backend endpoints directly with curl
4. Check CORS settings on backend

---

## Next Steps

### 1. Add Focal Persons to Projects
Update existing projects with actual focal person IDs:

```sql
-- Example: Assign first member as focal person for project #1
UPDATE public.projects
SET
  focal_person_id = (SELECT id FROM members LIMIT 1 OFFSET 0),
  focal_person_name = (SELECT name FROM members LIMIT 1 OFFSET 0),
  focal_person_email = (SELECT email FROM members LIMIT 1 OFFSET 0)
WHERE id = 1;
```

### 2. Create Project Dashboard
The dashboard should display:
- List of all projects with filters
- Priority-based sorting
- Resource allocation view
- Timeline visualization
- Budget tracking

### 3. Add Project Management Features
- Update project status
- Assign team members
- Track milestones
- Manage resources
- Update budgets

---

## Support

If you encounter issues:
1. Check Render.com logs: Dashboard → Your Service → Logs
2. Check Supabase logs: Dashboard → Logs
3. Review backend error traces
4. Test endpoints with the test script: `node test-backend-api.js`

---

## Summary Checklist

- [ ] Run migration `001_add_project_metadata.sql` on Supabase
- [ ] Run migration `002_seed_sample_projects.sql` on Supabase
- [ ] Verify 5 sample projects exist in database
- [ ] Update `DATABASE_URL` in local `.env`
- [ ] Update `DATABASE_URL` on Render.com
- [ ] Wait for Render to redeploy (2-3 minutes)
- [ ] Test backend locally with `python manage.py runserver`
- [ ] Test production backend with curl
- [ ] Test frontend at `http://localhost:3000/projects`
- [ ] Verify projects load from backend
- [ ] Assign focal persons to projects
- [ ] Create project dashboard (optional)

Once all steps are complete, your backend will be fully functional with comprehensive project metadata!
