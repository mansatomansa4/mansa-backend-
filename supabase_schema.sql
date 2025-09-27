-- Supabase schema alignment script
-- This script creates or alters tables to match the provided schema.
-- Review before running in production. Execute in Supabase SQL editor.

-- Enable required extensions
create extension if not exists "uuid-ossp";
create extension if not exists pgcrypto;

-- ADMIN TABLES
create table if not exists public.admins (
    id serial primary key,
    email varchar not null unique,
    password_hash varchar not null,
    name varchar not null,
    role varchar default 'admin',
    is_active boolean default true,
    last_login timestamp,
    created_at timestamp default current_timestamp,
    updated_at timestamp default current_timestamp
);

create table if not exists public.admin_audit_log (
    id serial primary key,
    admin_id integer references public.admins(id),
    action varchar not null,
    target_type varchar,
    target_id integer,
    details jsonb,
    ip_address inet,
    user_agent text,
    created_at timestamp default current_timestamp
);

-- MEMBERS CORE
create table if not exists public.members (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    email text not null,
    phone text not null,
    country text,
    city text,
    linkedin text,
    experience text,
    "areaOfExpertise" text,
    school text,
    level text,
    occupation text,
    jobtitle text,
    industry text,
    major text,
    gender text not null,
    membershiptype text not null,
    created_at timestamptz default now(),
    skills text,
    is_active boolean default true,
    updated_at timestamptz default now()
);

-- COMMUNITY MEMBERS (EXTENSION)
create table if not exists public.community_members (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    email text not null unique,
    phone text,
    joined_date timestamptz default now(),
    is_active boolean default true,
    profile_picture text,
    bio text,
    location text,
    skills text,
    created_at timestamptz default now(),
    updated_at timestamptz default now(),
    motivation text,
    constraint community_members_member_fk foreign key (id) references public.members(id)
);

-- PROJECTS
create table if not exists public.projects (
    id serial primary key,
    title text not null,
    description text,
    status text default 'Concept' check (status in ('Concept','Planning','Active','Completed')),
    location text,
    launch_date date,
    image_url text,
    project_type text default 'future' check (project_type in ('ongoing','future')),
    tags jsonb,
    participants_count integer default 0,
    max_participants integer,
    created_at timestamptz default now(),
    updated_at timestamptz default now(),
    member_id uuid
);

create table if not exists public.project_members (
    id uuid primary key default gen_random_uuid(),
    project_id integer not null,
    member_email text not null,
    member_name text not null,
    role text default 'Contributor',
    joined_date timestamptz default now(),
    is_active boolean default true,
    contribution_notes text,
    created_at timestamptz default now(),
    updated_at timestamptz default now(),
    member_id uuid references public.members(id)
);

create table if not exists public.project_applications (
    id uuid primary key default gen_random_uuid(),
    project_id integer not null,
    applicant_name text not null,
    applicant_email text not null,
    skills text,
    motivation text,
    status text default 'pending' check (status in ('pending','approved','rejected','withdrawn')),
    applied_date timestamptz default now(),
    reviewed_date timestamptz,
    reviewer_notes text,
    created_at timestamptz default now(),
    updated_at timestamptz default now(),
    member_id uuid references public.members(id)
);

-- EMAIL NOTIFICATIONS
create table if not exists public.email_notifications (
    id serial primary key,
    recipient_email varchar not null,
    recipient_name varchar,
    email_type varchar not null,
    subject text not null,
    template_used varchar,
    sent_by integer references public.admins(id),
    application_id uuid references public.project_applications(id),
    sent_at timestamp default current_timestamp,
    delivery_status varchar default 'sent',
    error_message text
);

-- Helpful indexes
create index if not exists idx_members_email on public.members(email);
create index if not exists idx_projects_status on public.projects(status);
create index if not exists idx_project_applications_status on public.project_applications(status);
create index if not exists idx_project_members_project on public.project_members(project_id);

-- Update triggers for updated_at timestamps could be added here.
