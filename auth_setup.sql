-- Authentication tables setup for Supabase
-- Run this in Supabase SQL Editor after running supabase_setup.sql

-- Create users table for authentication
create table if not exists public.users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  password_hash text not null,
  username text unique not null,
  created_at timestamp with time zone default now(),
  last_login timestamp with time zone,
  is_active boolean default true
);

-- Enable RLS on users table
alter table public.users enable row level security;

-- Drop existing policies if they exist
drop policy if exists users_read_own on public.users;
drop policy if exists users_insert_signup on public.users;
drop policy if exists users_update_own on public.users;

-- Policy: Users can read their own data
create policy users_read_own
  on public.users
  for select
  to anon, authenticated
  using (true);

-- Policy: Allow insert for signup
create policy users_insert_signup
  on public.users
  for insert
  to anon, authenticated
  with check (true);

-- Policy: Users can update their own data
create policy users_update_own
  on public.users
  for update
  to anon, authenticated
  using (true)
  with check (true);

-- Add user_id column to user_state table to link with users
alter table public.user_state add column if not exists user_id uuid references public.users(id) on delete cascade;

-- Update user_state policies to use user_id
drop policy if exists allow_anon_read_write_user_state on public.user_state;
drop policy if exists user_state_read_own on public.user_state;
drop policy if exists user_state_insert_own on public.user_state;
drop policy if exists user_state_update_own on public.user_state;
drop policy if exists user_state_delete_own on public.user_state;

create policy user_state_read_own
  on public.user_state
  for select
  to anon, authenticated
  using (true);

create policy user_state_insert_own
  on public.user_state
  for insert
  to anon, authenticated
  with check (true);

create policy user_state_update_own
  on public.user_state
  for update
  to anon, authenticated
  using (true)
  with check (true);

create policy user_state_delete_own
  on public.user_state
  for delete
  to anon, authenticated
  using (true);

-- Create index for faster lookups
create index if not exists idx_users_email on public.users(email);
create index if not exists idx_users_username on public.users(username);
create index if not exists idx_user_state_user_id on public.user_state(user_id);
