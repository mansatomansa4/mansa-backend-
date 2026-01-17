# Mentor Profile Management - User Guide

## Overview
This guide explains how mentors can manage their profiles, including editing information and uploading profile pictures.

## Features

### 1. View Mentor Profile
Mentees and other users can view detailed mentor profiles at:
```
/community/mentorship/{mentor_id}
```

**What's displayed:**
- Profile photo
- Bio and background
- Areas of expertise
- Professional information (company, job title)
- Years of experience
- Rating and session statistics
- Education and skills
- Social media links (LinkedIn, GitHub, Twitter)
- Contact information

### 2. Edit Mentor Profile
Mentors can edit their profiles at:
```
/community/mentorship/profile/edit
```

**Editable Fields:**
- **Bio**: Detailed description (minimum 50 characters)
- **Job Title**: Current position
- **Company**: Current employer
- **Years of Experience**: Total years in the field
- **Expertise**: Up to 10 areas (e.g., "Web Development", "Data Science")
- **Timezone**: For availability scheduling
- **Social Links**:
  - LinkedIn URL
  - GitHub URL  
  - Twitter URL

### 3. Upload Profile Photo

**Requirements:**
- File formats: JPG, JPEG, PNG, WebP
- Maximum size: 5 MB
- Recommended: Square images (400x400px)

**How to Upload:**
1. Go to **Edit Profile** page
2. Click **"Choose Photo"** button
3. Select an image from your computer
4. Preview appears immediately
5. Click **"Upload Photo"** to save
6. Photo is stored securely in Supabase storage

## API Endpoints

### For Developers

#### 1. Get Mentor Profile
```http
GET /api/v1/mentorship/mentors/{mentor_id}/
Authorization: Bearer {token}
```

**Response:**
```json
{
  "id": "uuid",
  "user_id": 1001,
  "bio": "Senior Software Engineer...",
  "photo_url": "https://...supabase.co/storage/v1/object/public/profile-pictures/mentors/...",
  "expertise": ["Web Development", "React", "Node.js"],
  "rating": 4.8,
  "total_sessions": 45,
  "company": "Google",
  "job_title": "Senior Engineer",
  "years_of_experience": 10,
  "linkedin_url": "https://linkedin.com/in/...",
  "github_url": "https://github.com/...",
  "twitter_url": "https://twitter.com/...",
  "availability_timezone": "UTC",
  "version": 1,
  "user": {
    "first_name": "Sarah",
    "last_name": "Johnson",
    "email": "sarah@example.com"
  }
}
```

#### 2. Update Mentor Profile
```http
PATCH /api/v1/mentorship/mentors/{mentor_id}/update_profile/
Authorization: Bearer {token}
Content-Type: application/json

{
  "bio": "Updated bio text...",
  "expertise": ["New", "Expertise", "Areas"],
  "company": "New Company",
  "job_title": "New Title",
  "years_of_experience": 12,
  "linkedin_url": "https://linkedin.com/in/newprofile",
  "version": 1
}
```

**Features:**
- **Optimistic Locking**: `version` field prevents concurrent update conflicts
- **Partial Updates**: Only send fields you want to change
- **Validation**: Backend validates all fields

**Response Codes:**
- `200`: Success
- `400`: Validation error
- `403`: Not authorized (not your profile)
- `409`: Version conflict (profile updated by another process)
- `500`: Server error

#### 3. Upload Profile Photo
```http
POST /api/v1/mentorship/mentors/{mentor_id}/upload_photo/
Authorization: Bearer {token}
Content-Type: multipart/form-data

photo: <file>
```

**Validation:**
- File type: image/jpeg, image/png, image/webp
- File size: Max 5 MB
- Ownership: Must be your profile

**Response:**
```json
{
  "photo_url": "https://...supabase.co/.../profile.jpg",
  "mentor": {
    "id": "uuid",
    "photo_url": "https://...",
    ...
  }
}
```

#### 4. Get Own Profile
```http
GET /api/v1/mentorship/mentors/my_profile/
Authorization: Bearer {token}
```

Returns the mentor profile for the currently logged-in user.

## Frontend Components

### Profile Edit Page
**Location**: `src/app/community/mentorship/profile/edit/page.tsx`

**Features:**
- Form validation
- Real-time character counter for bio
- Dynamic expertise tags (add/remove)
- Image preview before upload
- Optimistic locking with version control
- Success/error messages
- Auto-redirect after successful save

### Profile View Page
**Location**: `src/app/community/mentorship/[id]/page.tsx`

**Features:**
- Beautiful card-based layout
- Responsive design (mobile-friendly)
- Social media link integration
- Rating display with stars
- Session statistics
- "Book a Session" button
- Back navigation

## Workflow Examples

### Example 1: New Mentor Setup
```
1. User registers and is marked as mentor (is_mentor=true)
2. Mentor profile is created automatically in database
3. Mentor logs in and goes to /community/mentorship/profile/edit
4. Fills out bio, expertise, company info
5. Uploads profile picture
6. Clicks "Save Profile"
7. Profile is now visible to mentees
```

### Example 2: Update Profile Photo
```
1. Mentor logs in
2. Goes to /community/mentorship/profile/edit
3. Clicks "Choose Photo"
4. Selects new image from computer
5. Sees preview
6. Clicks "Upload Photo"
7. Old photo is replaced
8. New photo appears immediately
```

### Example 3: Mentee Views Profile
```
1. Mentee logs in
2. Browses /community/mentorship
3. Sees mentor cards with basic info
4. Clicks on a mentor card
5. Redirected to /community/mentorship/{mentor_id}
6. Views full profile with all details
7. Can book a session
```

## Best Practices

### For Mentors

**Bio Writing:**
- Start with your current role and experience
- Highlight what makes you unique
- Mention specific areas you can help with
- Include your mentoring philosophy
- Keep it conversational and friendly
- Aim for 100-500 words

**Expertise Selection:**
- Be specific (e.g., "React.js" vs just "Programming")
- List 5-7 core areas where you're strongest
- Include both technical and soft skills
- Match what mentees are searching for

**Profile Photo:**
- Use a professional headshot
- Ensure good lighting
- Smile and look approachable
- Avoid busy backgrounds
- Update regularly

**Professional Info:**
- Keep job title current
- Include well-known companies if applicable
- Update years of experience annually
- Link all active social profiles

### For Developers

**Performance:**
- Profile photos are cached via CDN
- API responses are cached for 5 minutes
- Use pagination for mentor listings
- Lazy load images

**Security:**
- Always validate user owns profile before updates
- Check file types and sizes
- Use optimistic locking for concurrent updates
- Sanitize user input

**Error Handling:**
- Show user-friendly error messages
- Log detailed errors server-side
- Handle network failures gracefully
- Provide retry options

## Troubleshooting

### "Not authorized to update this profile"
**Cause**: Trying to edit someone else's profile  
**Solution**: Only edit your own profile

### "Version mismatch" error
**Cause**: Profile was updated elsewhere  
**Solution**: Refresh page and try again

### Photo upload fails
**Causes**:
- File too large (>5 MB)
- Wrong file type
- Network issue

**Solutions**:
- Compress image
- Use JPG/PNG format
- Check internet connection

### Changes not saving
**Causes**:
- Validation errors
- Network timeout
- Session expired

**Solutions**:
- Check error messages
- Verify all required fields
- Re-login if needed

## Future Enhancements

### Planned Features
- [ ] Image cropping tool
- [ ] Bulk photo upload
- [ ] Video introductions
- [ ] Portfolio/work samples
- [ ] Mentor verification badges
- [ ] Profile completion percentage
- [ ] Analytics dashboard

### Under Consideration
- Profile templates
- AI-assisted bio writing
- Automated skill endorsements
- Profile sharing to social media
- QR code for profile

## Support

For technical support:
- Check backend logs: `apps/mentorship/views.py`
- Review Supabase storage logs
- Check browser console for errors
- Contact system administrator

For user support:
- Review this guide
- Check FAQ section
- Contact mentor support team
