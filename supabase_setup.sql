-- Run this once in Supabase SQL Editor

create table if not exists public.user_state (
  profile_name text primary key,
  data jsonb not null default '{}'::jsonb
);

alter table public.user_state enable row level security;

do $$
begin
  if not exists (
    select 1
    from pg_policies
    where schemaname = 'public'
      and tablename = 'user_state'
      and policyname = 'allow_anon_read_write_user_state'
  ) then
    create policy allow_anon_read_write_user_state
      on public.user_state
      for all
      to anon, authenticated
      using (true)
      with check (true);
  end if;
end
$$;
