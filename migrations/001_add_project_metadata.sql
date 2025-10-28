-- Migration: Add project metadata fields
-- Date: 2025-10-23
-- Description: Add objectives, deliverables, focal person, domain tags, priority, and resource fields to projects table

-- Add new columns to projects table
ALTER TABLE public.projects
ADD COLUMN IF NOT EXISTS objectives TEXT,
ADD COLUMN IF NOT EXISTS deliverables TEXT,
ADD COLUMN IF NOT EXISTS focal_person_id UUID,
ADD COLUMN IF NOT EXISTS focal_person_name TEXT,
ADD COLUMN IF NOT EXISTS focal_person_email TEXT,
ADD COLUMN IF NOT EXISTS domain_tags JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
ADD COLUMN IF NOT EXISTS resources_needed JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS human_skills_required TEXT,
ADD COLUMN IF NOT EXISTS platform_requirements TEXT,
ADD COLUMN IF NOT EXISTS devices_required TEXT,
ADD COLUMN IF NOT EXISTS timeline_start DATE,
ADD COLUMN IF NOT EXISTS timeline_end DATE,
ADD COLUMN IF NOT EXISTS budget_estimate NUMERIC(12,2),
ADD COLUMN IF NOT EXISTS current_budget NUMERIC(12,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS is_concurrent BOOLEAN DEFAULT false;

-- Add foreign key constraint for focal_person_id
ALTER TABLE public.projects
ADD CONSTRAINT fk_projects_focal_person
FOREIGN KEY (focal_person_id) REFERENCES public.members(id) ON DELETE SET NULL;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_projects_domain_tags ON public.projects USING gin (domain_tags);
CREATE INDEX IF NOT EXISTS idx_projects_priority ON public.projects (priority);
CREATE INDEX IF NOT EXISTS idx_projects_focal_person ON public.projects (focal_person_id);
CREATE INDEX IF NOT EXISTS idx_projects_timeline ON public.projects (timeline_start, timeline_end);

-- Add comment to columns
COMMENT ON COLUMN public.projects.objectives IS 'Project objectives and goals';
COMMENT ON COLUMN public.projects.deliverables IS 'Expected deliverables and outcomes';
COMMENT ON COLUMN public.projects.focal_person_id IS 'ID of the focal person/project lead';
COMMENT ON COLUMN public.projects.focal_person_name IS 'Name of the focal person (cached for performance)';
COMMENT ON COLUMN public.projects.focal_person_email IS 'Email of the focal person (cached for performance)';
COMMENT ON COLUMN public.projects.domain_tags IS 'Project domain tags (e.g., CyberSecurity, AI, ML, BIOTECH)';
COMMENT ON COLUMN public.projects.priority IS 'Project priority level based on available resources';
COMMENT ON COLUMN public.projects.resources_needed IS 'JSON object containing resource requirements';
COMMENT ON COLUMN public.projects.human_skills_required IS 'Human skills needed for project implementation';
COMMENT ON COLUMN public.projects.platform_requirements IS 'Platform requirements (software, cloud services, etc.)';
COMMENT ON COLUMN public.projects.devices_required IS 'Physical devices required';
COMMENT ON COLUMN public.projects.timeline_start IS 'Project start date';
COMMENT ON COLUMN public.projects.timeline_end IS 'Project expected completion date';
COMMENT ON COLUMN public.projects.budget_estimate IS 'Estimated budget for the project';
COMMENT ON COLUMN public.projects.current_budget IS 'Current allocated/spent budget';
COMMENT ON COLUMN public.projects.is_concurrent IS 'Whether this project can run concurrently with others';

-- Create a function to update focal_person cache when member data changes
CREATE OR REPLACE FUNCTION update_project_focal_person_cache()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE public.projects
  SET
    focal_person_name = NEW.name,
    focal_person_email = NEW.email,
    updated_at = NOW()
  WHERE focal_person_id = NEW.id;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to keep focal person data synced
DROP TRIGGER IF EXISTS trigger_update_project_focal_person ON public.members;
CREATE TRIGGER trigger_update_project_focal_person
AFTER UPDATE OF name, email ON public.members
FOR EACH ROW
WHEN (OLD.name IS DISTINCT FROM NEW.name OR OLD.email IS DISTINCT FROM NEW.email)
EXECUTE FUNCTION update_project_focal_person_cache();

-- Update existing projects with default values
UPDATE public.projects
SET
  domain_tags = COALESCE(domain_tags, '[]'::jsonb),
  priority = COALESCE(priority, 'medium'),
  resources_needed = COALESCE(resources_needed, '{}'::jsonb),
  current_budget = COALESCE(current_budget, 0),
  is_concurrent = COALESCE(is_concurrent, false)
WHERE domain_tags IS NULL
   OR priority IS NULL
   OR resources_needed IS NULL
   OR current_budget IS NULL
   OR is_concurrent IS NULL;
