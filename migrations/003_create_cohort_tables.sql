-- Migration: Create Research and Education Cohort Application Tables
-- Date: 2025-12-02
-- Description: Creates tables for storing cohort applications with email verification against members table

-- ============================================
-- RESEARCH COHORT APPLICATIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS research_cohort_applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Applicant Information (from members table verification)
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    name TEXT NOT NULL,
    phone TEXT,

    -- Research-specific fields
    research_interest TEXT NOT NULL,
    research_topic TEXT,
    research_experience TEXT,
    academic_background TEXT,
    current_institution TEXT,
    highest_qualification TEXT,
    field_of_study TEXT,
    publications TEXT,
    skills TEXT,
    motivation TEXT NOT NULL,
    availability TEXT,
    preferred_research_area TEXT,

    -- Application metadata
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'waitlist', 'withdrawn')),
    cohort_batch TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    reviewed_by UUID REFERENCES members(id),
    reviewer_notes TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Ensure one application per member per cohort batch
    UNIQUE(member_id, cohort_batch)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_research_cohort_email ON research_cohort_applications(email);
CREATE INDEX IF NOT EXISTS idx_research_cohort_status ON research_cohort_applications(status);
CREATE INDEX IF NOT EXISTS idx_research_cohort_member ON research_cohort_applications(member_id);
CREATE INDEX IF NOT EXISTS idx_research_cohort_batch ON research_cohort_applications(cohort_batch);

-- ============================================
-- EDUCATION COHORT APPLICATIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS education_cohort_applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Applicant Information (from members table verification)
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    name TEXT NOT NULL,
    phone TEXT,

    -- Education-specific fields
    education_interest TEXT NOT NULL,
    current_education_level TEXT,
    target_education_level TEXT,
    current_institution TEXT,
    field_of_study TEXT,
    learning_goals TEXT,
    skills_to_develop TEXT,
    prior_experience TEXT,
    preferred_learning_format TEXT,
    time_commitment TEXT,
    motivation TEXT NOT NULL,
    availability TEXT,

    -- Application metadata
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'waitlist', 'withdrawn')),
    cohort_batch TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    reviewed_by UUID REFERENCES members(id),
    reviewer_notes TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Ensure one application per member per cohort batch
    UNIQUE(member_id, cohort_batch)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_education_cohort_email ON education_cohort_applications(email);
CREATE INDEX IF NOT EXISTS idx_education_cohort_status ON education_cohort_applications(status);
CREATE INDEX IF NOT EXISTS idx_education_cohort_member ON education_cohort_applications(member_id);
CREATE INDEX IF NOT EXISTS idx_education_cohort_batch ON education_cohort_applications(cohort_batch);

-- ============================================
-- UPDATE TRIGGERS
-- ============================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_cohort_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for research cohort
DROP TRIGGER IF EXISTS trigger_research_cohort_updated_at ON research_cohort_applications;
CREATE TRIGGER trigger_research_cohort_updated_at
    BEFORE UPDATE ON research_cohort_applications
    FOR EACH ROW
    EXECUTE FUNCTION update_cohort_updated_at();

-- Trigger for education cohort
DROP TRIGGER IF EXISTS trigger_education_cohort_updated_at ON education_cohort_applications;
CREATE TRIGGER trigger_education_cohort_updated_at
    BEFORE UPDATE ON education_cohort_applications
    FOR EACH ROW
    EXECUTE FUNCTION update_cohort_updated_at();

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================

-- Enable RLS
ALTER TABLE research_cohort_applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE education_cohort_applications ENABLE ROW LEVEL SECURITY;

-- Policy: Allow public to insert (with member verification done at API level)
CREATE POLICY "Allow public insert for research cohort" ON research_cohort_applications
    FOR INSERT TO anon, authenticated
    WITH CHECK (true);

CREATE POLICY "Allow public insert for education cohort" ON education_cohort_applications
    FOR INSERT TO anon, authenticated
    WITH CHECK (true);

-- Policy: Allow authenticated users to view their own applications
CREATE POLICY "Users can view own research applications" ON research_cohort_applications
    FOR SELECT TO authenticated
    USING (auth.uid()::text = member_id::text);

CREATE POLICY "Users can view own education applications" ON education_cohort_applications
    FOR SELECT TO authenticated
    USING (auth.uid()::text = member_id::text);

-- Policy: Allow service role full access (for admin operations)
CREATE POLICY "Service role full access research" ON research_cohort_applications
    FOR ALL TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access education" ON education_cohort_applications
    FOR ALL TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================
-- COMMENTS
-- ============================================
COMMENT ON TABLE research_cohort_applications IS 'Stores applications for research cohort programs. Requires applicant to be a registered member.';
COMMENT ON TABLE education_cohort_applications IS 'Stores applications for education cohort programs. Requires applicant to be a registered member.';
COMMENT ON COLUMN research_cohort_applications.member_id IS 'Foreign key to members table - applicant must be a registered member';
COMMENT ON COLUMN education_cohort_applications.member_id IS 'Foreign key to members table - applicant must be a registered member';
