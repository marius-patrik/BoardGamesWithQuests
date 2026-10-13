-- Private authoritative persistence boundary for BoardGamesWithQuests.
-- G1 verifies compare-and-swap, membership, uniqueness, rollback and RLS.
-- Game legality is evaluated by the generic engine BEFORE invoking commit.
create schema if not exists bgwq;
revoke all on schema bgwq from public, anon, authenticated;
grant usage on schema bgwq to service_role;

create table if not exists bgwq.games (
  id uuid primary key default gen_random_uuid(),
  player_one uuid not null,
  player_two uuid not null,
  config_snapshot jsonb not null,
  state jsonb not null,
  revision bigint not null default 0 check (revision >= 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint distinct_participants check (player_one <> player_two),
  constraint config_is_object check (jsonb_typeof(config_snapshot) = 'object'),
  constraint state_is_object check (jsonb_typeof(state) = 'object')
);
create table if not exists bgwq.events (
  game_id uuid not null references bgwq.games(id) on delete cascade,
  revision bigint not null,
  actor uuid not null,
  payload jsonb not null,
  committed_at timestamptz not null default now(),
  primary key (game_id, revision),
  check (jsonb_typeof(payload) = 'object')
);
alter table bgwq.games enable row level security;
alter table bgwq.events enable row level security;
revoke all on bgwq.games, bgwq.events from public, anon, authenticated;
grant select, insert, update on bgwq.games to service_role;
grant select, insert on bgwq.events to service_role;

-- This is a private DB primitive, callable only by a trusted server-side role.
-- It intentionally does NOT decide move legality; the server must validate the
-- complete proposed state transition before calling this transaction primitive.
create or replace function bgwq.commit_revision(
  p_game uuid, p_actor uuid, p_expected bigint, p_state jsonb, p_event jsonb
) returns bigint
language plpgsql
security invoker
set search_path = ''
as $$
declare v_revision bigint;
begin
  if p_actor is null or p_expected is null or p_expected < 0
     or p_state is null or jsonb_typeof(p_state) <> 'object'
     or p_event is null or jsonb_typeof(p_event) <> 'object' then
    raise exception 'invalid commit arguments' using errcode='22023';
  end if;
  update bgwq.games
     set state=p_state, revision=revision+1, updated_at=now()
   where id=p_game and revision=p_expected
     and p_actor in (player_one, player_two)
   returning revision into v_revision;
  if not found then
    raise exception 'unauthorized or stale game revision' using errcode='40001';
  end if;
  insert into bgwq.events(game_id, revision, actor, payload)
  values (p_game, v_revision, p_actor, p_event);
  return v_revision;
end
$$;
revoke all on function bgwq.commit_revision(uuid,uuid,bigint,jsonb,jsonb)
 from public, anon, authenticated;
grant execute on function bgwq.commit_revision(uuid,uuid,bigint,jsonb,jsonb)
 to service_role;
