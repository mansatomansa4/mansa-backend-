-- SQL Script to Create users_user Table and Seed Test Users
-- Run this in your Supabase SQL Editor

-- Create users_user table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.users_user (
    id INTEGER PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    phone_number VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_user_email ON public.users_user(email);

-- Insert test users for the mentors we created
INSERT INTO public.users_user (id, email, first_name, last_name, phone_number, is_active) VALUES
(1001, 'sarah.johnson@example.com', 'Sarah', 'Johnson', '+1234567890', TRUE),
(1002, 'michael.chen@example.com', 'Michael', 'Chen', '+1234567891', TRUE),
(1003, 'amara.okafor@example.com', 'Amara', 'Okafor', '+1234567892', TRUE),
(1004, 'fatima.alhassan@example.com', 'Fatima', 'Al-Hassan', '+1234567893', TRUE),
(1005, 'james.mensah@example.com', 'James', 'Mensah', '+1234567894', TRUE),
(1006, 'priya.sharma@example.com', 'Priya', 'Sharma', '+1234567895', TRUE),
(1007, 'david.osei@example.com', 'David', 'Osei', '+1234567896', TRUE),
(1008, 'lisa.wang@example.com', 'Lisa', 'Wang', '+1234567897', TRUE),
(1009, 'kwame.boateng@example.com', 'Kwame', 'Boateng', '+1234567898', TRUE),
(1010, 'maria.rodriguez@example.com', 'Maria', 'Rodriguez', '+1234567899', TRUE)
ON CONFLICT (id) DO UPDATE SET
    first_name = EXCLUDED.first_name,
    last_name = EXCLUDED.last_name,
    email = EXCLUDED.email,
    updated_at = CURRENT_TIMESTAMP;

-- Verify the data
SELECT id, first_name, last_name, email FROM public.users_user ORDER BY id;
