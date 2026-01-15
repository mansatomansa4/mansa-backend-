# Mentorship Login Issue - Diagnosis and Fix

## Problem
Users attempting to login to the mentorship platform at `/community/mentorship/auth` receive a 404 error with the message "Email not found in database" even though they believe their email is registered.

## Root Cause
The email `wuniabdulai199@gmail.com` (or any other email showing this error) is **NOT actually present** in the Django `users_user` table in the Supabase database. The backend correctly returns a 404 when querying for a non-existent user.

## How the Email Login Works

1. User enters email on frontend: `/community/mentorship/auth`
2. Frontend calls: `POST /api/users/email-login/` with `{ email: "..." }`
3. Backend checks if user exists: `User.objects.get(email=email)`
4. If found: Returns JWT token + user info
5. If not found: Returns 404 error

## Solutions

### Option 1: Check and Add User via Django Shell (Recommended for Production)

```bash
# Connect to your production server (Render)
# Then run Django shell
python manage.py shell

# Check if user exists
from apps.users.models import User
email = 'wuniabdulai199@gmail.com'
try:
    user = User.objects.get(email=email)
    print(f"User found: {user.email} - ID: {user.id}")
except User.DoesNotExist:
    print(f"User NOT found: {email}")
    # Create the user
    user = User.objects.create_user(
        email=email,
        first_name='Wuni',
        last_name='Abdulai',
        is_mentee=True,
        approval_status='approved'
    )
    print(f"User created: {user.email} - ID: {user.id}")
```

### Option 2: Use Management Command

```bash
# Check if user exists
python manage.py check_user wuniabdulai199@gmail.com

# Create user if they don't exist
python manage.py check_user wuniabdulai199@gmail.com --create --first-name "Wuni" --last-name "Abdulai" --is-mentee
```

### Option 3: Use Python Script

```bash
# On the server where the backend is deployed
cd /path/to/mansa-backend
python add_test_user.py
```

This script will:
- Check if the user exists
- Create them if they don't
- Update their approval status to 'approved'
- Mark them as mentee/mentor as needed

### Option 4: Direct SQL in Supabase

Go to Supabase Dashboard → SQL Editor and run:

```sql
-- Check if user exists
SELECT id, email, first_name, last_name, is_mentor, is_mentee, approval_status
FROM users_user 
WHERE email = 'wuniabdulai199@gmail.com';

-- If not found, create the user
INSERT INTO users_user (
    email, first_name, last_name, password, role, 
    approval_status, is_mentor, is_mentee, is_active, 
    is_staff, is_superuser, date_joined
) VALUES (
    'wuniabdulai199@gmail.com',
    'Wuni',
    'Abdulai',
    'pbkdf2_sha256$600000$unusedpassword$dummy', -- Dummy password for email-only login
    'mentee',
    'approved',
    false,
    true,
    true,
    false,
    false,
    NOW()
);
```

## Verification Steps

After adding the user, verify:

1. **Check backend logs**: Login attempt should succeed
2. **Test login**: Go to https://www.mansa-to-mansa.org/community/mentorship/auth
3. **Enter email**: wuniabdulai199@gmail.com
4. **Expected result**: Successful login and redirect to mentorship dashboard

## Common Issues

### Issue: User exists but still gets 404
- **Cause**: Email case mismatch (e.g., `WuniAbdulai199@gmail.com` vs `wuniabdulai199@gmail.com`)
- **Solution**: Both frontend and backend normalize email to lowercase, but verify in database:
  ```sql
  SELECT email FROM users_user WHERE LOWER(email) = LOWER('wuniabdulai199@gmail.com');
  ```

### Issue: User created but approval_status is 'pending'
- **Cause**: Default approval status is 'pending', restricting access
- **Solution**: Update approval status:
  ```sql
  UPDATE users_user SET approval_status = 'approved' WHERE email = 'wuniabdulai199@gmail.com';
  ```

### Issue: User is created but is_mentee/is_mentor are both false
- **Cause**: User has no mentorship role assigned
- **Solution**: Update user role:
  ```sql
  UPDATE users_user SET is_mentee = true WHERE email = 'wuniabdulai199@gmail.com';
  ```

## Prevention

To avoid this issue in the future:

1. **User Registration Flow**: Implement a proper registration page where users can self-register
2. **Admin Dashboard**: Use the admin dashboard to pre-register users
3. **Bulk Import**: Create a script to bulk import users from a CSV file
4. **Better Error Messages**: Already improved in the latest frontend update

## Files Modified

1. **Backend**: 
   - `/apps/users/management/commands/check_user.py` - New management command
   - `/add_test_user.py` - Quick user creation script
   - `/migrations/check_and_add_user.sql` - SQL script for direct database access

2. **Frontend**: 
   - `/src/app/community/mentorship/auth/page.tsx` - Improved error messages

## Testing

To test the fix:

1. Add the user using one of the methods above
2. Go to: https://www.mansa-to-mansa.org/community/mentorship/auth
3. Enter: wuniabdulai199@gmail.com
4. Click "Continue"
5. Should redirect to mentorship dashboard

## Contact

If you continue to experience issues:
- Check backend logs for specific error messages
- Verify database connection to Supabase
- Ensure all migrations have been run: `python manage.py migrate`
