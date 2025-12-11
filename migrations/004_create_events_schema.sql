-- =============================================
-- Supabase Events Schema Migration
-- =============================================
-- This migration creates:
-- 1. Events table
-- 2. Event Images table
-- 3. Storage buckets for event flyers and photos
-- 4. Row Level Security (RLS) policies
-- 5. Storage policies
-- =============================================

-- =============================================
-- 1. CREATE EVENTS TABLE
-- =============================================

CREATE TABLE IF NOT EXISTS public.events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Basic Information
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL DEFAULT 'other',
    
    -- Event Details
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    location VARCHAR(255) NOT NULL,
    is_virtual BOOLEAN DEFAULT FALSE,
    virtual_link TEXT,
    
    -- Status & Capacity
    status VARCHAR(20) NOT NULL DEFAULT 'upcoming',
    max_attendees INTEGER,
    attendee_count INTEGER DEFAULT 0,
    
    -- Media
    flyer_url TEXT,
    
    -- Publishing
    published BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('upcoming', 'past')),
    CONSTRAINT valid_category CHECK (category IN ('networking', 'workshop', 'conference', 'webinar', 'social', 'fundraiser', 'other')),
    CONSTRAINT valid_attendees CHECK (attendee_count >= 0),
    CONSTRAINT valid_max_attendees CHECK (max_attendees IS NULL OR max_attendees > 0),
    CONSTRAINT valid_times CHECK (end_time > start_time)
);

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_events_status ON public.events(status);
CREATE INDEX IF NOT EXISTS idx_events_date ON public.events(date);
CREATE INDEX IF NOT EXISTS idx_events_published ON public.events(published);
CREATE INDEX IF NOT EXISTS idx_events_category ON public.events(category);
CREATE INDEX IF NOT EXISTS idx_events_status_published ON public.events(status, published);
CREATE INDEX IF NOT EXISTS idx_events_created_by ON public.events(created_by);

-- Add comment
COMMENT ON TABLE public.events IS 'Stores community events with details, dates, and media';

-- =============================================
-- 2. CREATE EVENT IMAGES TABLE
-- =============================================

CREATE TABLE IF NOT EXISTS public.event_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES public.events(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    caption VARCHAR(255),
    display_order INTEGER DEFAULT 0,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_display_order CHECK (display_order >= 0)
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_event_images_event_id ON public.event_images(event_id);
CREATE INDEX IF NOT EXISTS idx_event_images_order ON public.event_images(event_id, display_order);

-- Add comment
COMMENT ON TABLE public.event_images IS 'Stores multiple images/photos for each event';

-- =============================================
-- 3. CREATE STORAGE BUCKETS
-- =============================================

-- Create bucket for event flyers
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'event-flyers',
    'event-flyers',
    true,
    5242880, -- 5MB limit
    ARRAY['image/jpeg', 'image/png', 'image/jpg', 'image/webp', 'image/gif']
)
ON CONFLICT (id) DO NOTHING;

-- Create bucket for event photos
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'event-photos',
    'event-photos',
    true,
    5242880, -- 5MB limit
    ARRAY['image/jpeg', 'image/png', 'image/jpg', 'image/webp', 'image/gif']
)
ON CONFLICT (id) DO NOTHING;

-- =============================================
-- 4. CREATE UPDATED_AT TRIGGER FUNCTION
-- =============================================

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for events table
DROP TRIGGER IF EXISTS set_events_updated_at ON public.events;
CREATE TRIGGER set_events_updated_at
    BEFORE UPDATE ON public.events
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- =============================================
-- 5. CREATE AUTO-STATUS UPDATE FUNCTION
-- =============================================

-- Function to automatically update event status based on date
CREATE OR REPLACE FUNCTION public.auto_update_event_status()
RETURNS void AS $$
BEGIN
    UPDATE public.events
    SET status = 'past'
    WHERE date < CURRENT_DATE
    AND status = 'upcoming';
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- 6. ROW LEVEL SECURITY (RLS) POLICIES
-- =============================================

-- Enable RLS on events table
ALTER TABLE public.events ENABLE ROW LEVEL SECURITY;

-- Policy: Public can view published events
CREATE POLICY "Public users can view published events"
    ON public.events
    FOR SELECT
    USING (published = true);

-- Policy: Authenticated users can view all events
CREATE POLICY "Authenticated users can view all events"
    ON public.events
    FOR SELECT
    TO authenticated
    USING (true);

-- Policy: Authenticated users can insert events
CREATE POLICY "Authenticated users can create events"
    ON public.events
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = created_by);

-- Policy: Authenticated users can update their own events
CREATE POLICY "Users can update their own events"
    ON public.events
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = created_by)
    WITH CHECK (auth.uid() = created_by);

-- Policy: Authenticated users can delete their own events
CREATE POLICY "Users can delete their own events"
    ON public.events
    FOR DELETE
    TO authenticated
    USING (auth.uid() = created_by);

-- Enable RLS on event_images table
ALTER TABLE public.event_images ENABLE ROW LEVEL SECURITY;

-- Policy: Public can view images of published events
CREATE POLICY "Public can view images of published events"
    ON public.event_images
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.events
            WHERE events.id = event_images.event_id
            AND events.published = true
        )
    );

-- Policy: Authenticated users can view all event images
CREATE POLICY "Authenticated users can view all event images"
    ON public.event_images
    FOR SELECT
    TO authenticated
    USING (true);

-- Policy: Authenticated users can insert images for their events
CREATE POLICY "Users can add images to their events"
    ON public.event_images
    FOR INSERT
    TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.events
            WHERE events.id = event_images.event_id
            AND events.created_by = auth.uid()
        )
    );

-- Policy: Authenticated users can update images of their events
CREATE POLICY "Users can update images of their events"
    ON public.event_images
    FOR UPDATE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.events
            WHERE events.id = event_images.event_id
            AND events.created_by = auth.uid()
        )
    );

-- Policy: Authenticated users can delete images of their events
CREATE POLICY "Users can delete images of their events"
    ON public.event_images
    FOR DELETE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.events
            WHERE events.id = event_images.event_id
            AND events.created_by = auth.uid()
        )
    );

-- =============================================
-- 7. STORAGE POLICIES
-- =============================================

-- Event Flyers Storage Policies

-- Policy: Public can view event flyers
CREATE POLICY "Public Access to Event Flyers"
    ON storage.objects
    FOR SELECT
    USING (bucket_id = 'event-flyers');

-- Policy: Authenticated users can upload event flyers
CREATE POLICY "Authenticated users can upload event flyers"
    ON storage.objects
    FOR INSERT
    TO authenticated
    WITH CHECK (bucket_id = 'event-flyers');

-- Policy: Authenticated users can update their event flyers
CREATE POLICY "Authenticated users can update event flyers"
    ON storage.objects
    FOR UPDATE
    TO authenticated
    USING (bucket_id = 'event-flyers');

-- Policy: Authenticated users can delete their event flyers
CREATE POLICY "Authenticated users can delete event flyers"
    ON storage.objects
    FOR DELETE
    TO authenticated
    USING (bucket_id = 'event-flyers');

-- Event Photos Storage Policies

-- Policy: Public can view event photos
CREATE POLICY "Public Access to Event Photos"
    ON storage.objects
    FOR SELECT
    USING (bucket_id = 'event-photos');

-- Policy: Authenticated users can upload event photos
CREATE POLICY "Authenticated users can upload event photos"
    ON storage.objects
    FOR INSERT
    TO authenticated
    WITH CHECK (bucket_id = 'event-photos');

-- Policy: Authenticated users can update their event photos
CREATE POLICY "Authenticated users can update event photos"
    ON storage.objects
    FOR UPDATE
    TO authenticated
    USING (bucket_id = 'event-photos');

-- Policy: Authenticated users can delete their event photos
CREATE POLICY "Authenticated users can delete event photos"
    ON storage.objects
    FOR DELETE
    TO authenticated
    USING (bucket_id = 'event-photos');

-- =============================================
-- 8. CREATE HELPFUL VIEWS
-- =============================================

-- View for upcoming published events
CREATE OR REPLACE VIEW public.upcoming_events AS
SELECT 
    e.*,
    COUNT(ei.id) as image_count
FROM public.events e
LEFT JOIN public.event_images ei ON e.id = ei.event_id
WHERE e.published = true
AND e.status = 'upcoming'
AND e.date >= CURRENT_DATE
GROUP BY e.id
ORDER BY e.date ASC, e.start_time ASC;

-- View for past published events
CREATE OR REPLACE VIEW public.past_events AS
SELECT 
    e.*,
    COUNT(ei.id) as image_count
FROM public.events e
LEFT JOIN public.event_images ei ON e.id = ei.event_id
WHERE e.published = true
AND e.status = 'past'
GROUP BY e.id
ORDER BY e.date DESC, e.start_time DESC;

-- =============================================
-- 9. INSERT SAMPLE DATA (OPTIONAL)
-- =============================================

-- Insert sample events (uncomment if you want sample data)
/*
INSERT INTO public.events (title, description, category, date, start_time, end_time, location, status, published)
VALUES 
(
    'Annual Networking Gala 2025',
    'Join us for an evening of networking, celebration, and community building. Connect with professionals, students, and changemakers from across the globe.',
    'networking',
    '2025-12-20',
    '18:00:00',
    '22:00:00',
    'Virtual Event',
    'upcoming',
    true
),
(
    'Tech Innovation Workshop',
    'Learn about the latest trends in technology and innovation. Hands-on workshop with industry experts covering AI, blockchain, and emerging technologies.',
    'workshop',
    '2026-01-15',
    '14:00:00',
    '17:00:00',
    'Innovation Hub, New York',
    'upcoming',
    true
),
(
    'Community Leadership Summit',
    'A gathering of community leaders discussing strategies for impactful change and sustainable development in African communities worldwide.',
    'conference',
    '2025-11-10',
    '09:00:00',
    '16:00:00',
    'Conference Center, London',
    'past',
    true
);
*/

-- =============================================
-- 10. GRANT PERMISSIONS
-- =============================================

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO anon, authenticated;

-- Grant permissions on tables
GRANT ALL ON public.events TO authenticated;
GRANT SELECT ON public.events TO anon;

GRANT ALL ON public.event_images TO authenticated;
GRANT SELECT ON public.event_images TO anon;

-- Grant permissions on views
GRANT SELECT ON public.upcoming_events TO anon, authenticated;
GRANT SELECT ON public.past_events TO anon, authenticated;

-- =============================================
-- MIGRATION COMPLETE
-- =============================================

-- Verify migration
DO $$
BEGIN
    RAISE NOTICE '✅ Events table created successfully';
    RAISE NOTICE '✅ Event images table created successfully';
    RAISE NOTICE '✅ Storage buckets created (event-flyers, event-photos)';
    RAISE NOTICE '✅ RLS policies applied';
    RAISE NOTICE '✅ Storage policies applied';
    RAISE NOTICE '✅ Views created (upcoming_events, past_events)';
    RAISE NOTICE '✅ Migration completed successfully!';
    RAISE NOTICE '';
    RAISE NOTICE '📝 Next Steps:';
    RAISE NOTICE '1. Configure your app to use Supabase URL and anon key';
    RAISE NOTICE '2. Set up authentication';
    RAISE NOTICE '3. Start uploading events through the dashboard';
END $$;
