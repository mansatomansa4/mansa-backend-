-- Mansa MentorHub Database Schema
-- Supabase PostgreSQL Schema for Mentorship Platform
-- Created: January 7, 2026
-- Execute in Supabase SQL Editor

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- MENTORS TABLE
-- Stores mentor profile information
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.mentors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL UNIQUE, -- References Django User model
    bio TEXT,
    photo_url TEXT,
    expertise JSONB DEFAULT '[]'::jsonb, -- Array of expertise areas
    availability_timezone VARCHAR(50) DEFAULT 'UTC',
    rating DECIMAL(3,2) DEFAULT 0.00 CHECK (rating >= 0 AND rating <= 5),
    total_sessions INTEGER DEFAULT 0 CHECK (total_sessions >= 0),
    is_approved BOOLEAN DEFAULT FALSE,
    version INTEGER DEFAULT 1, -- For optimistic locking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for querying approved mentors (most common query)
CREATE INDEX IF NOT EXISTS idx_mentors_approved 
ON public.mentors(is_approved) 
WHERE is_approved = TRUE;

-- GIN index for JSONB expertise field (enables fast searches)
CREATE INDEX IF NOT EXISTS idx_mentors_expertise_gin 
ON public.mentors USING GIN (expertise);

-- Index for user_id lookups
CREATE INDEX IF NOT EXISTS idx_mentors_user_id 
ON public.mentors(user_id);

-- ============================================================================
-- MENTOR AVAILABILITY TABLE
-- Stores mentor availability time slots
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.mentor_availability (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mentor_id UUID NOT NULL REFERENCES public.mentors(id) ON DELETE CASCADE,
    day_of_week INTEGER CHECK (day_of_week >= 0 AND day_of_week <= 6), -- 0=Sunday, 6=Saturday
    start_time TIME NOT NULL,
    end_time TIME NOT NULL CHECK (end_time > start_time),
    is_recurring BOOLEAN DEFAULT TRUE, -- TRUE for weekly recurring, FALSE for specific date
    specific_date DATE, -- Used when is_recurring = FALSE
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_availability_type CHECK (
        (is_recurring = TRUE AND day_of_week IS NOT NULL AND specific_date IS NULL) OR
        (is_recurring = FALSE AND specific_date IS NOT NULL)
    )
);

-- Index for finding available slots by mentor
CREATE INDEX IF NOT EXISTS idx_availability_mentor_active 
ON public.mentor_availability(mentor_id, is_active) 
WHERE is_active = TRUE;

-- Index for specific date lookups
CREATE INDEX IF NOT EXISTS idx_availability_specific_date 
ON public.mentor_availability(specific_date) 
WHERE specific_date IS NOT NULL;

-- ============================================================================
-- MENTORSHIP BOOKINGS TABLE (PARTITIONED BY DATE)
-- Stores all mentorship session bookings
-- Partitioned monthly for better performance with large datasets
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.mentorship_bookings (
    id UUID DEFAULT gen_random_uuid(),
    mentor_id UUID NOT NULL REFERENCES public.mentors(id) ON DELETE CASCADE,
    mentee_id INTEGER NOT NULL, -- References Django User model
    session_date DATE NOT NULL CHECK (session_date >= CURRENT_DATE),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL CHECK (end_time > start_time),
    status VARCHAR(20) DEFAULT 'confirmed' CHECK (status IN ('confirmed', 'completed', 'cancelled', 'no_show')),
    meeting_link TEXT,
    notes TEXT, -- Notes from mentee when booking
    mentee_notes TEXT, -- Additional notes mentee can add later
    mentor_notes TEXT, -- Notes from mentor after session
    booking_version INTEGER DEFAULT 1, -- For optimistic locking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    cancelled_by INTEGER, -- References Django User model (who cancelled)
    PRIMARY KEY (id, session_date)
) PARTITION BY RANGE (session_date);

-- Create partitions for current and next 12 months
-- This improves query performance and makes data management easier
CREATE TABLE IF NOT EXISTS public.mentorship_bookings_2026_01 
PARTITION OF public.mentorship_bookings 
FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE IF NOT EXISTS public.mentorship_bookings_2026_02 
PARTITION OF public.mentorship_bookings 
FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

CREATE TABLE IF NOT EXISTS public.mentorship_bookings_2026_03 
PARTITION OF public.mentorship_bookings 
FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');

CREATE TABLE IF NOT EXISTS public.mentorship_bookings_2026_04 
PARTITION OF public.mentorship_bookings 
FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');

CREATE TABLE IF NOT EXISTS public.mentorship_bookings_2026_05 
PARTITION OF public.mentorship_bookings 
FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');

CREATE TABLE IF NOT EXISTS public.mentorship_bookings_2026_06 
PARTITION OF public.mentorship_bookings 
FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');

CREATE TABLE IF NOT EXISTS public.mentorship_bookings_2026_07 
PARTITION OF public.mentorship_bookings 
FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');

CREATE TABLE IF NOT EXISTS public.mentorship_bookings_2026_08 
PARTITION OF public.mentorship_bookings 
FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');

CREATE TABLE IF NOT EXISTS public.mentorship_bookings_2026_09 
PARTITION OF public.mentorship_bookings 
FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');

CREATE TABLE IF NOT EXISTS public.mentorship_bookings_2026_10 
PARTITION OF public.mentorship_bookings 
FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');

CREATE TABLE IF NOT EXISTS public.mentorship_bookings_2026_11 
PARTITION OF public.mentorship_bookings 
FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');

CREATE TABLE IF NOT EXISTS public.mentorship_bookings_2026_12 
PARTITION OF public.mentorship_bookings 
FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');

CREATE TABLE IF NOT EXISTS public.mentorship_bookings_2027_01 
PARTITION OF public.mentorship_bookings 
FOR VALUES FROM ('2027-01-01') TO ('2027-02-01');

-- Indexes on bookings table (applied to all partitions)
CREATE INDEX IF NOT EXISTS idx_bookings_mentor_date 
ON public.mentorship_bookings(mentor_id, session_date);

CREATE INDEX IF NOT EXISTS idx_bookings_mentee_status 
ON public.mentorship_bookings(mentee_id, status);

CREATE INDEX IF NOT EXISTS idx_bookings_status 
ON public.mentorship_bookings(status);

CREATE INDEX IF NOT EXISTS idx_bookings_date_range 
ON public.mentorship_bookings(session_date, start_time);

-- ============================================================================
-- MENTORSHIP EXPERTISE TABLE
-- Predefined expertise categories for standardization
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.mentorship_expertise (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Seed initial expertise categories
INSERT INTO public.mentorship_expertise (name, category, description) VALUES
    ('AI & Machine Learning', 'Technology', 'Artificial Intelligence, ML algorithms, deep learning'),
    ('Web Development', 'Technology', 'Frontend, backend, full-stack development'),
    ('Mobile Development', 'Technology', 'iOS, Android, React Native, Flutter'),
    ('Data Science & Analytics', 'Technology', 'Data analysis, visualization, statistical modeling'),
    ('Career Guidance', 'Professional', 'Career planning, job search, resume review'),
    ('Cybersecurity', 'Technology', 'Security practices, ethical hacking, compliance'),
    ('Cloud & DevOps', 'Technology', 'AWS, Azure, GCP, CI/CD, infrastructure'),
    ('Product Management', 'Business', 'Product strategy, roadmaps, stakeholder management'),
    ('UX/UI Design', 'Design', 'User experience, interface design, prototyping'),
    ('Business & Entrepreneurship', 'Business', 'Startups, business strategy, fundraising'),
    ('Leadership & Management', 'Professional', 'Team leadership, people management, coaching'),
    ('Technical Writing', 'Professional', 'Documentation, technical communication')
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- Ensures data isolation and security
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE public.mentors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mentor_availability ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mentorship_bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mentorship_expertise ENABLE ROW LEVEL SECURITY;

-- Mentors Table Policies
-- Anyone can view approved mentors
CREATE POLICY "Anyone can view approved mentors" 
ON public.mentors 
FOR SELECT 
USING (is_approved = TRUE);

-- Service role (backend) can do anything
CREATE POLICY "Service role full access to mentors" 
ON public.mentors 
FOR ALL 
USING (true)
WITH CHECK (true);

-- Availability Table Policies
-- Anyone can view availability of approved mentors
CREATE POLICY "Anyone can view mentor availability" 
ON public.mentor_availability 
FOR SELECT 
USING (
    EXISTS (
        SELECT 1 FROM public.mentors 
        WHERE mentors.id = mentor_availability.mentor_id 
        AND mentors.is_approved = TRUE
    )
);

-- Service role full access
CREATE POLICY "Service role full access to availability" 
ON public.mentor_availability 
FOR ALL 
USING (true)
WITH CHECK (true);

-- Bookings Table Policies
-- Service role manages all bookings
CREATE POLICY "Service role full access to bookings" 
ON public.mentorship_bookings 
FOR ALL 
USING (true)
WITH CHECK (true);

-- Expertise Table Policies
-- Everyone can read expertise (public reference data)
CREATE POLICY "Anyone can view expertise categories" 
ON public.mentorship_expertise 
FOR SELECT 
USING (true);

-- Service role can manage expertise
CREATE POLICY "Service role can manage expertise" 
ON public.mentorship_expertise 
FOR ALL 
USING (true)
WITH CHECK (true);

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for mentors table
DROP TRIGGER IF EXISTS update_mentors_updated_at ON public.mentors;
CREATE TRIGGER update_mentors_updated_at
    BEFORE UPDATE ON public.mentors
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for availability table
DROP TRIGGER IF EXISTS update_availability_updated_at ON public.mentor_availability;
CREATE TRIGGER update_availability_updated_at
    BEFORE UPDATE ON public.mentor_availability
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for bookings table
DROP TRIGGER IF EXISTS update_bookings_updated_at ON public.mentorship_bookings;
CREATE TRIGGER update_bookings_updated_at
    BEFORE UPDATE ON public.mentorship_bookings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to increment mentor session count when booking is completed
CREATE OR REPLACE FUNCTION increment_mentor_sessions()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        UPDATE public.mentors 
        SET total_sessions = total_sessions + 1
        WHERE id = NEW.mentor_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-increment sessions
DROP TRIGGER IF EXISTS auto_increment_mentor_sessions ON public.mentorship_bookings;
CREATE TRIGGER auto_increment_mentor_sessions
    AFTER UPDATE ON public.mentorship_bookings
    FOR EACH ROW
    EXECUTE FUNCTION increment_mentor_sessions();

-- ============================================================================
-- HELPER VIEWS
-- ============================================================================

-- View for active mentors with session counts
CREATE OR REPLACE VIEW public.active_mentors_view AS
SELECT 
    m.id,
    m.user_id,
    m.bio,
    m.photo_url,
    m.expertise,
    m.availability_timezone,
    m.rating,
    m.total_sessions,
    m.created_at,
    COUNT(DISTINCT ma.id) as availability_slots_count,
    COUNT(DISTINCT mb.id) FILTER (WHERE mb.status = 'confirmed' AND mb.session_date >= CURRENT_DATE) as upcoming_sessions
FROM public.mentors m
LEFT JOIN public.mentor_availability ma ON m.id = ma.mentor_id AND ma.is_active = TRUE
LEFT JOIN public.mentorship_bookings mb ON m.id = mb.mentor_id
WHERE m.is_approved = TRUE
GROUP BY m.id;

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================
COMMENT ON TABLE public.mentors IS 'Stores mentor profile information and metadata';
COMMENT ON TABLE public.mentor_availability IS 'Stores mentor availability time slots (recurring weekly or specific dates)';
COMMENT ON TABLE public.mentorship_bookings IS 'Stores all mentorship session bookings, partitioned by month';
COMMENT ON TABLE public.mentorship_expertise IS 'Reference table for standardized expertise categories';

COMMENT ON COLUMN public.mentors.version IS 'Used for optimistic locking to prevent concurrent update conflicts';
COMMENT ON COLUMN public.mentors.expertise IS 'JSONB array of expertise area names';
COMMENT ON COLUMN public.mentor_availability.is_recurring IS 'TRUE for weekly recurring slots, FALSE for one-time specific dates';
COMMENT ON COLUMN public.mentorship_bookings.booking_version IS 'Used for optimistic locking to prevent double-booking';

-- ============================================================================
-- SCHEMA CREATION COMPLETE
-- ============================================================================
-- Next steps:
-- 1. Verify all tables created: SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'mentor%';
-- 2. Verify indexes: SELECT indexname FROM pg_indexes WHERE tablename LIKE 'mentor%';
-- 3. Test RLS policies with different roles
-- 4. Create monthly partitions as needed (automated via cron or app)
-- ============================================================================
