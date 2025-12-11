# Supabase Events System Setup Guide

## 📋 Prerequisites
- Supabase project created at https://supabase.com
- Supabase CLI installed (optional, for local development)

## 🚀 Quick Setup (Via Supabase Dashboard)

### Step 1: Run the Migration

1. **Go to your Supabase Dashboard:**
   - Visit https://supabase.com/dashboard
   - Select your project

2. **Open SQL Editor:**
   - Click "SQL Editor" in the left sidebar
   - Click "New Query"

3. **Copy and Paste:**
   - Open the file: `mansa-backend/migrations/004_create_events_schema.sql`
   - Copy ALL the content
   - Paste into the SQL Editor

4. **Execute:**
   - Click "Run" or press Ctrl+Enter
   - Wait for success message
   - You should see: ✅ Migration completed successfully!

### Step 2: Verify the Setup

1. **Check Tables:**
   - Go to "Table Editor" in the sidebar
   - You should see:
     - ✅ `events` table
     - ✅ `event_images` table

2. **Check Storage:**
   - Go to "Storage" in the sidebar
   - You should see:
     - ✅ `event-flyers` bucket (public)
     - ✅ `event-photos` bucket (public)

3. **Check Policies:**
   - Go to "Authentication" → "Policies"
   - Verify RLS policies are active for both tables

## 🔧 Configuration

### Step 3: Get Your Supabase Credentials

1. **Go to Project Settings:**
   - Click the gear icon (⚙️) at bottom left
   - Go to "API" section

2. **Copy these values:**
   ```
   Project URL: https://xxxxxxxxxxxxx.supabase.co
   anon/public key: eyJhbGc...
   service_role key: eyJhbGc... (keep secret!)
   ```

### Step 4: Update Environment Variables

**For Frontend (`mansa-redesign/.env.local`):**
```env
NEXT_PUBLIC_SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...your-anon-key...
```

**For Dashboard (`Mansa-dashboard/.env.local`):**
```env
NEXT_PUBLIC_SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...your-anon-key...
```

## 📝 Usage Examples

### Creating an Event (TypeScript)

```typescript
import { createClient } from '@supabase/supabase-js'
import { Database } from '@/types/supabase-events'

const supabase = createClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

// Create event
const { data, error } = await supabase
  .from('events')
  .insert({
    title: 'Tech Workshop 2025',
    description: 'Learn React and Next.js',
    category: 'workshop',
    date: '2025-12-15',
    start_time: '14:00:00',
    end_time: '17:00:00',
    location: 'Virtual',
    is_virtual: true,
    published: true
  })
  .select()
```

### Uploading Event Flyer

```typescript
// Upload flyer
const file = event.target.files[0]
const fileName = `${eventId}-${Date.now()}.jpg`

const { data: uploadData, error: uploadError } = await supabase
  .storage
  .from('event-flyers')
  .upload(fileName, file)

if (uploadData) {
  // Get public URL
  const { data: { publicUrl } } = supabase
    .storage
    .from('event-flyers')
    .getPublicUrl(fileName)
  
  // Update event with flyer URL
  await supabase
    .from('events')
    .update({ flyer_url: publicUrl })
    .eq('id', eventId)
}
```

### Fetching Published Events

```typescript
// Get upcoming published events
const { data: events } = await supabase
  .from('upcoming_events') // Using view
  .select('*')
  .order('date', { ascending: true })

// Or using the table directly
const { data: upcomingEvents } = await supabase
  .from('events')
  .select(`
    *,
    event_images (*)
  `)
  .eq('published', true)
  .eq('status', 'upcoming')
  .gte('date', new Date().toISOString().split('T')[0])
  .order('date', { ascending: true })
```

## 🔒 Security Features

### What's Protected:
- ✅ RLS (Row Level Security) enabled on all tables
- ✅ Public users can only see published events
- ✅ Authenticated users can create/edit their own events
- ✅ Storage buckets are public for read, auth-only for write
- ✅ Automatic timestamp updates
- ✅ Data validation via CHECK constraints

### Storage Limits:
- Max file size: 5MB per file
- Allowed formats: JPEG, PNG, WebP, GIF
- Auto-optimized on upload

## 🔄 Auto-Updates

The system automatically:
- Updates `updated_at` timestamp on every change
- Can move events from upcoming → past (via function)

### Run Status Update Manually:
```sql
SELECT auto_update_event_status();
```

### Schedule Auto-Update (Supabase Dashboard):
1. Go to "Database" → "Extensions"
2. Enable `pg_cron` extension
3. Create cron job:
```sql
SELECT cron.schedule(
  'update-event-status',
  '0 0 * * *', -- Run daily at midnight
  $$SELECT auto_update_event_status()$$
);
```

## 📊 Sample Data

To insert sample events, uncomment section 9 in the migration file or run:

```sql
INSERT INTO public.events (title, description, category, date, start_time, end_time, location, status, published)
VALUES 
(
    'Annual Networking Gala 2025',
    'Join us for an evening of networking and celebration.',
    'networking',
    '2025-12-20',
    '18:00:00',
    '22:00:00',
    'Virtual Event',
    'upcoming',
    true
);
```

## 🐛 Troubleshooting

### Issue: "Permission denied for schema public"
**Solution:** The migration grants the necessary permissions. Re-run section 10 of the migration.

### Issue: "Bucket already exists"
**Solution:** Normal. The `ON CONFLICT DO NOTHING` handles this. Your buckets are already created.

### Issue: "RLS policy already exists"
**Solution:** Drop existing policies first:
```sql
DROP POLICY IF EXISTS "policy_name" ON public.events;
```
Then re-run the migration.

### Issue: "Storage upload fails"
**Solution:** 
1. Check file size (must be < 5MB)
2. Check file type (must be image)
3. Verify storage policies are applied
4. Check authentication status

## 📱 Testing

### Test via SQL Editor:
```sql
-- Check tables
SELECT * FROM events LIMIT 5;
SELECT * FROM event_images LIMIT 5;

-- Check views
SELECT * FROM upcoming_events;
SELECT * FROM past_events;

-- Check storage buckets
SELECT * FROM storage.buckets WHERE id IN ('event-flyers', 'event-photos');
```

### Test via API:
```bash
# Get events (replace with your URL and key)
curl 'https://xxxxx.supabase.co/rest/v1/events?published=eq.true' \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Authorization: Bearer YOUR_ANON_KEY"
```

## ✅ Checklist

- [ ] Migration executed successfully
- [ ] Tables created (events, event_images)
- [ ] Storage buckets created (event-flyers, event-photos)
- [ ] RLS policies active
- [ ] Storage policies active
- [ ] Environment variables configured
- [ ] TypeScript types file in place
- [ ] Test event created and visible

## 🎉 You're Ready!

Your Supabase events system is now fully configured and ready to use. Head to your dashboard to start creating events!

## 📚 Additional Resources

- [Supabase Docs](https://supabase.com/docs)
- [Supabase Storage Guide](https://supabase.com/docs/guides/storage)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)
