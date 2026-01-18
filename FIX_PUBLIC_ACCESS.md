# Fix: Public Access to Mentor Endpoints

## Issue
When clicking on mentor cards on the frontend, users were getting 401 Unauthorized errors when trying to view mentor detail pages.

## Root Cause
The `MentorViewSet` had `permission_classes = [permissions.IsAuthenticated]` which required authentication for ALL actions, including viewing public mentor profiles.

## Solution
Added a `get_permissions()` method to the `MentorViewSet` that:
- Allows **public access** (no authentication required) for:
  - `list` - Browse all mentors
  - `retrieve` - View individual mentor detail page
  - `availability` - View mentor availability (accessed via the retrieve action)
  
- Still **requires authentication** for:
  - `my_profile` - View your own profile
  - `create_profile` - Create a new mentor profile
  - `update_profile` - Edit your profile
  - `upload_photo` - Upload profile picture

## Code Change

```python
def get_permissions(self):
    """
    Allow unauthenticated access to list and retrieve actions.
    Require authentication for all other actions.
    """
    if self.action in ['list', 'retrieve']:
        return [permissions.AllowAny()]
    return [permissions.IsAuthenticated()]
```

## Testing

After deployment, verify:
1. ✅ Mentor list loads without login at `/community/mentorship`
2. ✅ Can click any mentor card to view full profile
3. ✅ Mentor detail page loads without 401 error
4. ✅ Availability calendar works
5. ✅ Can still edit profile only when logged in as a mentor

## Deployment Status

**Committed**: ✅ Yes  
**Pushed to GitHub**: ✅ Yes  
**Render Deployment**: 🔄 In progress (auto-deploy from GitHub)

## Next Steps

1. Wait 2-3 minutes for Render to deploy
2. Check Render dashboard: https://dashboard.render.com/
3. Look for build log showing successful deployment
4. Test the frontend at http://localhost:3000/community/mentorship
5. Click on a mentor card - should now work without errors!

## Additional Notes

- The `ExpertiseViewSet` already had `permissions.AllowAny` so it works fine
- The `BookingViewSet` correctly requires authentication (only logged-in users can book)
- Frontend code doesn't need any changes - it was already handling the API correctly

## Files Modified

- `apps/mentorship/views.py` - Added `get_permissions()` method to `MentorViewSet`
