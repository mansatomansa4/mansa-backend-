-- =====================================================
-- PROJECT APPLICANTS QUERIES
-- =====================================================

-- 1. LIST OF APPLICANTS UNDER EACH PROJECT WITH EMAIL AND PHONE
-- This query shows all applicants for each project including their contact info
SELECT 
    p.id as project_id,
    p.title as project_name,
    p.status as project_status,
    p.project_type,
    pa.id as application_id,
    pa.applicant_name,
    pa.applicant_email,
    m.phone as applicant_phone,
    pa.skills,
    pa.motivation,
    pa.status as application_status,
    pa.applied_date,
    pa.reviewed_date,
    pa.reviewer_notes
FROM projects p
LEFT JOIN project_applications pa ON p.id = pa.project_id
LEFT JOIN members m ON pa.member_id = m.id
ORDER BY p.title, pa.applied_date DESC;

-- Alternative: Only show projects that have applicants
SELECT 
    p.id as project_id,
    p.title as project_name,
    p.status as project_status,
    pa.applicant_name,
    pa.applicant_email,
    m.phone as applicant_phone,
    pa.status as application_status,
    pa.applied_date
FROM projects p
INNER JOIN project_applications pa ON p.id = pa.project_id
LEFT JOIN members m ON pa.member_id = m.id
ORDER BY p.title, pa.applied_date DESC;


-- =====================================================
-- 2. VIEW: PROJECT NAME AND NUMBER OF APPLICANTS
-- =====================================================

-- Create a view for easy querying
CREATE OR REPLACE VIEW project_applicants_summary AS
SELECT 
    p.id as project_id,
    p.title as project_name,
    p.status as project_status,
    p.project_type,
    p.location,
    p.launch_date,
    COUNT(pa.id) as total_applicants,
    COUNT(CASE WHEN pa.status = 'pending' THEN 1 END) as pending_applicants,
    COUNT(CASE WHEN pa.status = 'approved' THEN 1 END) as approved_applicants,
    COUNT(CASE WHEN pa.status = 'rejected' THEN 1 END) as rejected_applicants,
    COUNT(CASE WHEN pa.status = 'withdrawn' THEN 1 END) as withdrawn_applicants,
    p.max_participants,
    p.participants_count
FROM projects p
LEFT JOIN project_applications pa ON p.id = pa.project_id
GROUP BY 
    p.id, 
    p.title, 
    p.status, 
    p.project_type, 
    p.location, 
    p.launch_date,
    p.max_participants,
    p.participants_count
ORDER BY total_applicants DESC;

-- Query the view
SELECT * FROM project_applicants_summary;

-- Query the view with filters
SELECT * FROM project_applicants_summary 
WHERE project_status = 'Active' 
ORDER BY total_applicants DESC;


-- =====================================================
-- ADDITIONAL USEFUL QUERIES
-- =====================================================

-- Get projects with most pending applications
SELECT 
    project_name,
    pending_applicants,
    total_applicants
FROM project_applicants_summary
WHERE pending_applicants > 0
ORDER BY pending_applicants DESC;

-- Get detailed applicant list for a specific project
SELECT 
    pa.applicant_name,
    pa.applicant_email,
    m.phone,
    m.country,
    m.city,
    m.linkedin,
    m.areaOfExpertise,
    pa.skills,
    pa.motivation,
    pa.status,
    pa.applied_date
FROM project_applications pa
LEFT JOIN members m ON pa.member_id = m.id
WHERE pa.project_id = 1  -- Replace with your project ID
ORDER BY pa.applied_date DESC;

-- Get projects that are over capacity
SELECT 
    project_name,
    total_applicants,
    max_participants,
    (total_applicants - max_participants) as over_capacity_by
FROM project_applicants_summary
WHERE max_participants IS NOT NULL 
  AND total_applicants > max_participants
ORDER BY over_capacity_by DESC;

-- Get application statistics by status
SELECT 
    pa.status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM project_applications pa
GROUP BY pa.status
ORDER BY count DESC;
