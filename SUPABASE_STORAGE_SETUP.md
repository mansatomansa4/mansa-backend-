# Supabase Storage Bucket Setup for Profile Pictures

## Overview
This guide walks through setting up a Supabase Storage bucket to store mentor and mentee profile pictures.

## Steps to Create Storage Bucket

### 1. Access Supabase Dashboard
1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project: `Mansa-to-Mansa`
3. Click on **Storage** in the left sidebar

### 2. Create Profile Pictures Bucket
1. Click the **"New bucket"** button
2. Configure the bucket:
   - **Name**: `profile-pictures`
   - **Public bucket**: ✅ Enable (allows public access to URLs)
   - **File size limit**: 5 MB (recommended)
   - **Allowed MIME types**: `image/jpeg`, `image/jpg`, `image/png`, `image/webp`

3. Click **"Create bucket"**

### 3. Set Bucket Policies (Optional - for more control)

If you need fine-grained control, add these policies:

```sql
-- Allow authenticated users to upload their own profile pictures
CREATE POLICY "Users can upload their profile pictures"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'profile-pictures' AND
  auth.uid()::text = (storage.foldername(name))[1]
);

-- Allow public read access
CREATE POLICY "Public can view profile pictures"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'profile-pictures');

-- Allow users to update their own pictures
CREATE POLICY "Users can update their profile pictures"
ON storage.objects FOR UPDATE
TO authenticated
USING (
  bucket_id = 'profile-pictures' AND
  auth.uid()::text = (storage.foldername(name))[1]
);

-- Allow users to delete their own pictures
CREATE POLICY "Users can delete their profile pictures"
ON storage.objects FOR DELETE
TO authenticated
USING (
  bucket_id = 'profile-pictures' AND
  auth.uid()::text = (storage.foldername(name))[1]
);
```

### 4. Verify Bucket Setup
1. Go to **Storage** > **profile-pictures**
2. Try uploading a test image through the Supabase dashboard
3. Copy the public URL and verify it's accessible

## Folder Structure

The application organizes files in the bucket as follows:

```
profile-pictures/
├── mentors/
│   ├── mentor_{uuid}_{hash}.jpg
│   ├── mentor_{uuid}_{hash}.png
│   └── ...
└── mentees/
    ├── mentee_{uuid}_{hash}.jpg
    ├── mentee_{uuid}_{hash}.png
    └── ...
```

## Backend Integration

The backend is already configured to use this bucket. Key files:

- **Upload function**: `apps/mentorship/supabase_client.py:upload_mentor_photo()`
- **Delete function**: `apps/mentorship/supabase_client.py:delete_mentor_photo()`
- **Upload endpoint**: `/api/v1/mentorship/mentors/{id}/upload_photo/`

## Frontend Integration

Profile editing pages have been created:

- **Mentor profile edit**: `/community/mentorship/profile/edit`
- **Photo upload component**: Integrated in the edit page

## File Upload Specifications

### Accepted Formats
- JPEG/JPG
- PNG
- WebP

### File Size Limits
- Maximum: 5 MB per file
- Recommended: < 2 MB for optimal performance

### Image Requirements
- Minimum dimensions: 200x200 px
- Recommended: 400x400 px (square)
- Aspect ratio: 1:1 (square) preferred

## Testing the Setup

### 1. Test Photo Upload via API

```bash
# Get your access token first (after login)
TOKEN="your_jwt_token"
MENTOR_ID="your_mentor_uuid"

# Upload photo
curl -X POST \
  "${API_URL}/api/v1/mentorship/mentors/${MENTOR_ID}/upload_photo/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "photo=@/path/to/your/photo.jpg"
```

### 2. Test via Frontend
1. Log in as a mentor
2. Navigate to `/community/mentorship/profile/edit`
3. Click "Choose Photo" and select an image
4. Click "Upload Photo"
5. Verify the photo appears in your profile

## Troubleshooting

### Issue: "Bucket not found" error
**Solution**: Ensure the bucket name is exactly `profile-pictures` (with hyphen, not underscore)

### Issue: "Permission denied" error
**Solution**: 
- Check that the bucket is set to "Public"
- Verify RLS policies are correctly configured
- Ensure the user is authenticated

### Issue: "File too large" error
**Solution**: 
- Reduce image file size
- Compress the image using tools like TinyPNG
- Ensure image is under 5 MB

### Issue: Images not displaying
**Solution**:
- Check that the public URL is correctly formatted
- Verify CORS settings in Supabase
- Check browser console for errors

## Security Considerations

1. **File Type Validation**: Backend validates MIME types
2. **File Size Limits**: Enforced at backend level (5 MB max)
3. **Unique Filenames**: UUID-based naming prevents collisions
4. **Ownership Verification**: Users can only upload to their own profile

## Maintenance

### Clean Up Old Images
When a user uploads a new profile picture, the old one can be deleted:

```python
# In your backend code
if mentor.photo_url:
    supabase_client.delete_mentor_photo(mentor.photo_url)
```

### Monitor Storage Usage
- Check storage usage in Supabase Dashboard
- Supabase free tier includes 1 GB storage
- Upgrade plan if needed

## Next Steps

1. ✅ Create the `profile-pictures` bucket in Supabase Dashboard
2. ✅ Set bucket to public
3. ✅ Test photo upload via frontend
4. Create similar setup for mentees if needed
5. Implement image compression on upload (optional)
6. Add image cropping tool (optional enhancement)

## Support

If you encounter issues:
- Check Supabase logs in the Dashboard
- Review backend logs for API errors
- Check browser console for frontend errors
- Verify environment variables are set correctly
