-- Script to check if user exists and add them if needed
-- Run this in your Supabase SQL Editor or via psql

-- 1. Check if the user exists
SELECT 
    id, 
    email, 
    first_name, 
    last_name, 
    role, 
    is_mentor, 
    is_mentee, 
    approval_status,
    date_joined
FROM users_user 
WHERE email = 'wuniabdulai199@gmail.com';

-- 2. If user doesn't exist, create them (uncomment and modify as needed)
/*
INSERT INTO users_user (
    email,
    first_name,
    last_name,
    password,  -- Django uses pbkdf2_sha256 hashing, this is a dummy since we use passwordless login
    role,
    approval_status,
    is_mentor,
    is_mentee,
    is_active,
    is_staff,
    is_superuser,
    date_joined
) VALUES (
    'wuniabdulai199@gmail.com',
    'Wuni',  -- Change this to actual first name
    'Abdulai',  -- Change this to actual last name
    'pbkdf2_sha256$600000$unusedpassword$dummy',  -- Dummy password since we use email login
    'mentee',  -- or 'mentor', 'user', 'admin'
    'approved',
    false,  -- is_mentor: set to true if they are a mentor
    true,   -- is_mentee: set to true if they are a mentee
    true,   -- is_active
    false,  -- is_staff
    false,  -- is_superuser
    NOW()   -- date_joined
);
*/

-- 3. Verify user was created
SELECT 
    id, 
    email, 
    first_name, 
    last_name, 
    role, 
    is_mentor, 
    is_mentee, 
    approval_status
FROM users_user 
WHERE email = 'wuniabdulai199@gmail.com';

-- 4. Optional: Update existing user to be a mentee/mentor
/*
UPDATE users_user 
SET 
    is_mentee = true,
    approval_status = 'approved'
WHERE email = 'wuniabdulai199@gmail.com';
*/
