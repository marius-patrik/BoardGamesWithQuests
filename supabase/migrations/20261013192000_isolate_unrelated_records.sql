-- Restrict unrelated records to a non-exposed schema while retaining user data.
-- Supabase Auth identities remain intact; game access uses the private bgwq schema.
create schema if not exists retained_records;
revoke all on schema retained_records from public, anon, authenticated;
drop trigger if exists on_auth_user_created on auth.users;
drop trigger if exists on_account_created on public.accounts;
drop function if exists public.handle_new_user();
drop function if exists public.create_user_resources();
drop table if exists public.profiles;
drop table if exists public.player_stats;
drop table if exists public.admins;
alter table public.wallets set schema retained_records;
alter table public.game_stats set schema retained_records;
alter table public.accounts set schema retained_records;
revoke all on all tables in schema retained_records from public, anon, authenticated;
revoke all on all sequences in schema retained_records from public, anon, authenticated;
alter default privileges in schema retained_records
  revoke all on tables from public, anon, authenticated;
