-- SQL script to add missing mentor fields to users_user table
-- Run this directly on your production database if migrations haven't applied

-- Add is_mentor column
ALTER TABLE users_user 
ADD COLUMN IF NOT EXISTS is_mentor BOOLEAN DEFAULT FALSE;

-- Add is_mentee column
ALTER TABLE users_user 
ADD COLUMN IF NOT EXISTS is_mentee BOOLEAN DEFAULT FALSE;

-- Add mentor_approved_at column
ALTER TABLE users_user 
ADD COLUMN IF NOT EXISTS mentor_approved_at TIMESTAMP WITH TIME ZONE NULL;

-- Update the columns to not be null with default values
UPDATE users_user SET is_mentor = FALSE WHERE is_mentor IS NULL;
UPDATE users_user SET is_mentee = FALSE WHERE is_mentee IS NULL;

-- Add comments for documentation
COMMENT ON COLUMN users_user.is_mentor IS 'User is registered as a mentor';
COMMENT ON COLUMN users_user.is_mentee IS 'User is registered as a mentee';
COMMENT ON COLUMN users_user.mentor_approved_at IS 'When mentor application was approved';
