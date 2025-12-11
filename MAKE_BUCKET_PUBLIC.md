# How to Make Your Supabase Storage Bucket Public

## The Problem
Your project images are returning 400 errors because the `project-images` bucket is not public. It needs public access for the images to display on your websites.

## Steps to Fix

### 1. Go to Supabase Dashboard
Visit: https://supabase.com/dashboard/project/adnteftmqytcnieqmlma/storage/buckets

### 2. Find the `project-images` Bucket
- You should see it in the list of buckets
- Click on the bucket name

### 3. Make it Public
**Option A: Via Bucket Settings**
1. Click the ⚙️ (settings/gear icon) next to the bucket name
2. Look for "Public bucket" toggle
3. Turn it **ON**
4. Save changes

**Option B: Via Configuration**
1. Click on the bucket
2. Go to "Configuration" or "Settings" tab
3. Find "Public Access" setting
4. Enable public access
5. Save

### 4. Set Public Policy (if needed)
If there's a "Policies" tab:
1. Click "Policies"
2. Click "New Policy"
3. Select "For public read access"
4. Apply to `project-images` bucket
5. Save

## Alternative: Quick Policy SQL

If you have SQL access, run this in the SQL Editor:

```sql
-- Make project-images bucket public for reading
CREATE POLICY "Public Access"
ON storage.objects FOR SELECT
USING ( bucket_id = 'project-images' );
```

## After Making it Public

1. The URLs will work:
   `https://adnteftmqytcnieqmlma.supabase.co/storage/v1/object/public/project-images/ai.jpeg`

2. Test one URL in your browser to confirm

3. Refresh your dashboard at `http://localhost:4000/dashboard/projects`

4. Images should now display!

## Security Note

Making the bucket public means anyone with the URL can view the images. This is typically fine for:
- Project thumbnails
- Public website images
- Marketing materials

If you need private images, we'd need to implement signed URLs instead.

## Current Image Files in Bucket

From your screenshot, you have:
- ai.jpeg
- archive.jpeg
- SECURITY.jpeg
- africa.jpeg
- census.jpeg
- census3.jpeg
- library.jpeg
- library2.jpeg
- election2.jpeg
- job2.jpeg
- mapping.jpeg
- vendors.jpg
- mobility.jpg
- disease.jpeg
- drugs.jpg
- map.jpeg
- cargo.jpg
- And more...

All these will be accessible once the bucket is public!
