-- Private invitation lifecycle and idempotent authoritative session transactions.
-- Supabase JWT verification and game legality remain trusted server obligations.
alter table bgwq.games alter column player_two drop not null;
alter table bgwq.games add column lifecycle text not null default 'active';
alter table bgwq.games add column create_action_id text;
alter table bgwq.games add constraint game_lifecycle check (
  (lifecycle = 'pending' and player_two is null and revision = 0 and state = '{}'::jsonb)
  or (lifecycle = 'active' and player_two is not null)
);
alter table bgwq.games add constraint create_action_is_bounded check (
  create_action_id is null or char_length(create_action_id) between 1 and 128
);
create unique index bgwq_unique_create_action on bgwq.games(player_one, create_action_id)
  where create_action_id is not null;

-- Referential identity checks require no service-role SELECT on auth.users.
-- Restrictive references never delete, alter or cascade into Auth identities.
alter table bgwq.games add constraint player_one_auth_identity
  foreign key (player_one) references auth.users(id) not valid;
alter table bgwq.games add constraint player_two_auth_identity
  foreign key (player_two) references auth.users(id) not valid;
alter table bgwq.events add constraint event_actor_auth_identity
  foreign key (actor) references auth.users(id) not valid;
alter table bgwq.games validate constraint player_one_auth_identity;
alter table bgwq.games validate constraint player_two_auth_identity;
alter table bgwq.events validate constraint event_actor_auth_identity;

alter table bgwq.events add column action_id text;
alter table bgwq.events add column action_scope text;
alter table bgwq.events add column state_hash bytea;
alter table bgwq.events add constraint event_action_is_bounded check (
  action_id is null or char_length(action_id) between 1 and 128
);
alter table bgwq.events add constraint event_state_hash_size check (
  state_hash is null or octet_length(state_hash) = 32
);
alter table bgwq.events add constraint event_action_scope check (
  case
    when action_scope is null then action_id is null and state_hash is null
    when action_scope = 'activation' then action_id is not null and state_hash is not null and revision = 0
    when action_scope = 'domain' then action_id is not null and state_hash is not null and revision between 1 and 4096
    else false
  end
);
create unique index bgwq_unique_game_action on bgwq.events(game_id, action_scope, action_id)
  where action_scope is not null;

create function bgwq.validate_session_square(p_square jsonb, p_board jsonb)
returns void language plpgsql security invoker set search_path = '' as $$
declare coordinate jsonb;
begin
  if jsonb_typeof(p_square) is distinct from 'array' then
    raise exception 'square must be a JSON array' using errcode = '22023';
  end if;
  if jsonb_array_length(p_square) <> 2 then
    raise exception 'square requires exactly two coordinates' using errcode = '22023';
  end if;
  for coordinate in select value from jsonb_array_elements(p_square) loop
    if jsonb_typeof(coordinate) is distinct from 'number'
       or coordinate::text !~ '^(0|[1-9][0-9]{0,2})$' then
      raise exception 'square coordinates must be nonnegative bounded integers' using errcode = '22023';
    end if;
  end loop;
  if (p_square->>0)::integer >= (p_board->>'rows')::integer
     or (p_square->>1)::integer >= (p_board->>'columns')::integer then
    raise exception 'square is outside configured board dimensions' using errcode = '22023';
  end if;
end $$;

create function bgwq.validate_session_snapshot(
  p_game uuid, p_one uuid, p_two uuid, p_config jsonb, p_revision bigint, p_state jsonb
) returns void
language plpgsql security invoker set search_path = '' as $$
declare field text; value jsonb; piece jsonb; occupied jsonb[] := array[]::jsonb[];
begin
  if jsonb_typeof(p_state) is distinct from 'object'
     or octet_length(p_state::text) > 4194304
     or (select array_agg(key order by key) from jsonb_object_keys(p_state) key)
        is distinct from array[
          'active_side','board','captured','clocks','config','events','game_id',
          'halfmove_count','outcome','participants','position_history','quest_progress',
          'revision','rule_state','special_rights','started_at_ms','temporary_targets','version'
        ]::text[] then
    raise exception 'invalid session snapshot envelope' using errcode = '22023';
  end if;
  if jsonb_typeof(p_state->'version') is distinct from 'number'
     or p_state->>'version' is distinct from '1'
     or jsonb_typeof(p_state->'revision') is distinct from 'number'
     or p_state->>'game_id' is distinct from p_game::text
     or p_state->>'revision' is distinct from p_revision::text
     or (p_state->'config')::text is distinct from p_config::text
     or p_state->'participants' is distinct from
        jsonb_build_object('1', p_one::text, '-1', p_two::text)
     or jsonb_typeof(p_state->'active_side') is distinct from 'number'
     or p_state->>'active_side' not in ('1', '-1') then
    raise exception 'session identity, configuration or revision mismatch' using errcode = '22023';
  end if;
  if p_config ? 'starting_side' and (
    jsonb_typeof(p_config->'starting_side') is distinct from 'number'
    or p_config->>'starting_side' not in ('1','-1')
  ) then
    raise exception 'configured starting side must be a strict canonical side' using errcode = '22023';
  end if;
  if p_revision = 0 and p_state->>'active_side' is distinct from coalesce(p_config->>'starting_side','1') then
    raise exception 'genesis turn must match the pinned configuration' using errcode = '22023';
  end if;
  if jsonb_typeof(p_config->'pieces') is distinct from 'object'
     or jsonb_typeof(p_state->'clocks') is distinct from 'object'
     or (select array_agg(key order by key) from jsonb_object_keys(p_state->'clocks') key)
        is distinct from array['anchor_ms','increment_ms','remaining_ms']::text[]
     or jsonb_typeof(p_state->'clocks'->'remaining_ms') is distinct from 'object'
     or (select array_agg(key order by key) from jsonb_object_keys(p_state->'clocks'->'remaining_ms') key)
        is distinct from array['-1','1']::text[]
     or (select array_agg(key order by key) from jsonb_object_keys(p_state->'quest_progress') key)
        is distinct from (select array_agg(key order by key) from unnest(array[p_one::text,p_two::text]) key) then
    raise exception 'participant-scoped metadata is malformed' using errcode = '22023';
  end if;
  foreach field in array array['rows','columns'] loop
    value := p_config->'board'->field;
    if jsonb_typeof(value) is distinct from 'number'
       or value::text !~ '^[1-9][0-9]{0,2}$' or value::numeric > 256 then
      raise exception 'configuration board dimensions are invalid' using errcode = '22023';
    end if;
  end loop;
  foreach field in array array['anchor_ms','increment_ms'] loop
    value := p_state->'clocks'->field;
    if jsonb_typeof(value) is distinct from 'number' or value::text !~ '^(0|[1-9][0-9]*)$' then
      raise exception 'clock metadata must be nonnegative integers' using errcode = '22023';
    end if;
  end loop;
  foreach field in array array['1','-1'] loop
    value := p_state->'clocks'->'remaining_ms'->field;
    if jsonb_typeof(value) is distinct from 'number' or value::text !~ '^(0|[1-9][0-9]*)$' then
      raise exception 'participant clocks must be nonnegative integers' using errcode = '22023';
    end if;
  end loop;
  foreach field in array array['board','captured','events','position_history'] loop
    if jsonb_typeof(p_state->field) is distinct from 'array' then
      raise exception 'session field % must be an array', field using errcode = '22023';
    end if;
  end loop;
  if jsonb_array_length(p_state->'board') > 2048 or jsonb_array_length(p_state->'captured') > 2048 then
    raise exception 'piece records exceed the supported configuration capacity' using errcode = '22023';
  end if;
  foreach field in array array['board','captured'] loop
    for piece in select entry from jsonb_array_elements(p_state->field) entry loop
      if jsonb_typeof(piece) is distinct from 'object' then
        raise exception 'piece record must be an object' using errcode = '22023';
      end if;
      if (select array_agg(key order by key) from jsonb_object_keys(piece) key)
          is distinct from (case field when 'board' then array['kind','moved','side','square'] else array['kind','side'] end)
         or jsonb_typeof(piece->'kind') is distinct from 'string'
         or not (p_config->'pieces' ? (piece->>'kind'))
         or jsonb_typeof(piece->'side') is distinct from 'number'
         or piece->>'side' not in ('1','-1') then
        raise exception 'piece metadata must use configured kinds and strict sides' using errcode = '22023';
      end if;
      if field = 'board' then
        if jsonb_typeof(piece->'moved') is distinct from 'boolean' then
          raise exception 'piece movement flag must be boolean' using errcode = '22023';
        end if;
        perform bgwq.validate_session_square(piece->'square', p_config->'board');
        if piece->'square' = any(occupied) then
          raise exception 'piece squares must be distinct' using errcode = '22023';
        end if;
        occupied := array_append(occupied, piece->'square');
      end if;
    end loop;
  end loop;
  foreach field in array array['clocks','rule_state','special_rights','temporary_targets','quest_progress'] loop
    if jsonb_typeof(p_state->field) is distinct from 'object' then
      raise exception 'session field % must be an object', field using errcode = '22023';
    end if;
  end loop;
  if p_revision < 0 or p_revision > 4096
     or jsonb_array_length(p_state->'events') <> p_revision
     or jsonb_typeof(p_state->'outcome') not in ('object', 'null')
     or jsonb_typeof(p_state->'halfmove_count') is distinct from 'number'
     or p_state->>'halfmove_count' !~ '^(0|[1-9][0-9]*)$'
     or jsonb_typeof(p_state->'started_at_ms') is distinct from 'number'
     or p_state->>'started_at_ms' !~ '^(0|[1-9][0-9]*)$'
     or (p_state->>'started_at_ms')::numeric > 9007199254740991 then
    raise exception 'invalid session history or scalar metadata' using errcode = '22023';
  end if;
end $$;

create or replace function bgwq.prevent_snapshot_mutation()
returns trigger language plpgsql security invoker set search_path = '' as $$
begin
  if new.id is distinct from old.id
     or new.player_one is distinct from old.player_one
     or new.config_snapshot::text is distinct from old.config_snapshot::text
     or new.created_at is distinct from old.created_at
     or new.create_action_id is distinct from old.create_action_id then
    raise exception 'game identity and configuration are immutable' using errcode = '23514';
  end if;
  if old.lifecycle = 'pending' and new.lifecycle = 'active'
     and old.player_two is null and new.player_two is not null then
    perform bgwq.validate_session_snapshot(
      new.id, new.player_one, new.player_two, new.config_snapshot, 0, new.state
    );
    if new.revision <> 0 or new.state->>'active_side' is distinct from coalesce(new.config_snapshot->>'starting_side','1') then
      raise exception 'activation must start at revision zero and the configured side' using errcode = '23514';
    end if;
  elsif new.player_two is distinct from old.player_two or new.lifecycle is distinct from old.lifecycle then
    raise exception 'active participants and lifecycle are immutable' using errcode = '23514';
  end if;
  return new;
end $$;

create function bgwq.create_game(p_game uuid, p_actor uuid, p_action text, p_config jsonb)
returns uuid language plpgsql security invoker set search_path = '' as $$
declare existing bgwq.games%rowtype;
begin
  if p_game is null or p_actor is null or p_action is null
     or char_length(p_action) not between 1 and 128
     or jsonb_typeof(p_config) is distinct from 'object'
     or jsonb_typeof(p_config->'schema_version') is distinct from 'number'
     or p_config->>'schema_version' is distinct from '2'
     or octet_length(p_config::text) > 1048576 then
    raise exception 'invalid game creation arguments' using errcode = '22023';
  end if;
  if p_config ? 'starting_side' and (
    jsonb_typeof(p_config->'starting_side') is distinct from 'number'
    or p_config->>'starting_side' not in ('1','-1')
  ) then
    raise exception 'configured starting side must be a strict canonical side' using errcode = '22023';
  end if;
  insert into bgwq.games(id, player_one, player_two, config_snapshot, state, lifecycle, create_action_id)
  values (p_game, p_actor, null, p_config, '{}'::jsonb, 'pending', p_action)
  on conflict do nothing;
  select * into existing from bgwq.games
    where player_one = p_actor and create_action_id = p_action for update;
  if not found or existing.id <> p_game or existing.config_snapshot::text <> p_config::text then
    raise exception 'creation action or game identity has a conflicting request' using errcode = '23505';
  end if;
  return existing.id;
end $$;

create function bgwq.activate_game(p_game uuid, p_actor uuid, p_action text, p_state jsonb)
returns bigint language plpgsql security invoker set search_path = '' as $$
declare game bgwq.games%rowtype; existing bgwq.events%rowtype; fingerprint bytea;
begin
  if p_game is null or p_actor is null or p_action is null
     or char_length(p_action) not between 1 and 128
     or jsonb_typeof(p_state) is distinct from 'object' then
    raise exception 'invalid activation arguments' using errcode = '22023';
  end if;
  select * into game from bgwq.games where id = p_game for update;
  if not found or p_actor = game.player_one then
    raise exception 'unknown game or invalid joining participant' using errcode = '42501';
  end if;
  fingerprint := pg_catalog.sha256(pg_catalog.convert_to(p_state::text, 'UTF8'));
  select * into existing from bgwq.events where game_id = p_game and action_scope = 'activation' and action_id = p_action;
  if found then
    if existing.revision = 0 and existing.actor = p_actor
       and existing.payload->>'kind' = 'activation' and existing.state_hash = fingerprint then
      return 0;
    end if;
    raise exception 'activation action has a conflicting request' using errcode = '23505';
  end if;
  if game.lifecycle <> 'pending' then
    raise exception 'participant slot is already occupied' using errcode = '55000';
  end if;
  perform bgwq.validate_session_snapshot(p_game, game.player_one, p_actor, game.config_snapshot, 0, p_state);
  if p_state->>'active_side' is distinct from coalesce(game.config_snapshot->>'starting_side','1') or p_state->'outcome' <> 'null'::jsonb
     or p_state->'clocks'->>'anchor_ms' is distinct from p_state->>'started_at_ms'
     or (p_state->'clocks'->>'increment_ms')::numeric is distinct from (game.config_snapshot->'clock'->>'increment_seconds')::numeric * 1000
     or (p_state->'clocks'->'remaining_ms'->>'1')::numeric is distinct from (game.config_snapshot->'clock'->>'initial_seconds')::numeric * 1000
     or (p_state->'clocks'->'remaining_ms'->>'-1')::numeric is distinct from (game.config_snapshot->'clock'->>'initial_seconds')::numeric * 1000 then
    raise exception 'activation must begin with the configured side and no outcome' using errcode = '22023';
  end if;
  update bgwq.games set player_two = p_actor, lifecycle = 'active', state = p_state, updated_at = now()
    where id = p_game;
  insert into bgwq.events(game_id, revision, actor, payload, action_scope, action_id, state_hash)
  values (p_game, 0, p_actor, jsonb_build_object('kind','activation','action_id',p_action,'state',p_state), 'activation', p_action, fingerprint);
  return 0;
end $$;

create or replace function bgwq.commit_revision(
  p_game uuid, p_actor uuid, p_expected bigint, p_state jsonb, p_event jsonb
) returns bigint language plpgsql security invoker set search_path = '' as $$
declare game bgwq.games%rowtype; existing bgwq.events%rowtype; action text; fingerprint bytea; side text; point jsonb; previous jsonb;
begin
  if p_game is null or p_actor is null or p_expected is null or p_expected < 0 or p_expected >= 4096
     or jsonb_typeof(p_state) is distinct from 'object'
     or jsonb_typeof(p_event) is distinct from 'object'
     or jsonb_typeof(p_event->'action_id') is distinct from 'string'
     or char_length(p_event->>'action_id') not between 1 and 128 then
    raise exception 'invalid commit arguments' using errcode = '22023';
  end if;
  if (select array_agg(key order by key) from jsonb_object_keys(p_event) key)
       is distinct from array['action_id','actor','at_ms','captured','effects','expected_revision','move','outcome','revision']::text[]
     or jsonb_typeof(p_event->'at_ms') is distinct from 'number'
     or p_event->>'at_ms' !~ '^(0|[1-9][0-9]*)$'
     or (p_event->>'at_ms')::numeric > 9007199254740991
     or jsonb_typeof(p_event->'captured') is distinct from 'array'
     or jsonb_typeof(p_event->'effects') is distinct from 'array' then
    raise exception 'invalid domain event envelope' using errcode = '22023';
  end if;
  action := p_event->>'action_id';
  select * into game from bgwq.games where id = p_game for update;
  if not found or (p_actor <> game.player_one and (game.player_two is null or p_actor <> game.player_two)) then
    raise exception 'actor is not a game participant' using errcode = '42501';
  end if;
  if game.lifecycle <> 'active' or game.create_action_id is null
     or not exists (
       select 1 from bgwq.events where game_id = p_game and revision = 0
         and action_scope = 'activation' and action_id is not null and payload->>'kind' = 'activation' and state_hash is not null
     ) then
    raise exception 'game requires authenticated activation and keyed events' using errcode = '55000';
  end if;
  fingerprint := pg_catalog.sha256(pg_catalog.convert_to(p_state::text, 'UTF8'));
  select * into existing from bgwq.events where game_id = p_game and action_scope = 'domain' and action_id = action;
  if found then
    if existing.revision = p_expected + 1 and existing.actor = p_actor
       and existing.payload::text = p_event::text and existing.state_hash = fingerprint then
      return existing.revision;
    end if;
    raise exception 'action identifier has a conflicting request' using errcode = '23505';
  end if;
  if game.revision <> p_expected then
    raise exception 'stale game revision' using errcode = '40001';
  end if;
  perform bgwq.validate_session_snapshot(p_game, game.player_one, game.player_two, game.config_snapshot, game.revision, game.state);
  side := game.state->>'active_side';
  if p_actor <> (case side when '1' then game.player_one else game.player_two end) then
    raise exception 'actor does not control the active turn' using errcode = '42501';
  end if;
  if game.state->'outcome' <> 'null'::jsonb then
    raise exception 'game has a terminal outcome' using errcode = '55000';
  end if;
  perform bgwq.validate_session_snapshot(p_game, game.player_one, game.player_two, game.config_snapshot, p_expected + 1, p_state);
  if p_state->>'active_side' is distinct from (-(side::integer))::text
     or p_event->>'actor' is distinct from p_actor::text
     or jsonb_typeof(p_event->'expected_revision') is distinct from 'number'
     or jsonb_typeof(p_event->'revision') is distinct from 'number'
     or p_event->>'expected_revision' is distinct from p_expected::text
     or p_event->>'revision' is distinct from (p_expected + 1)::text
     or (p_event->'outcome')::text is distinct from (p_state->'outcome')::text
     or (p_state->'events')->(p_expected::integer) is distinct from p_event
     or ((p_state->'events') - (p_expected::integer))::text is distinct from (game.state->'events')::text
     or (p_event->>'at_ms')::numeric < (game.state->'clocks'->>'anchor_ms')::numeric
     or p_state->'clocks'->>'anchor_ms' is distinct from p_event->>'at_ms'
     or p_state->'clocks'->>'increment_ms' is distinct from game.state->'clocks'->>'increment_ms'
     or p_state->>'started_at_ms' is distinct from game.state->>'started_at_ms' then
    raise exception 'event does not match the authoritative transition' using errcode = '22023';
  end if;
  if jsonb_typeof(p_event->'move') is distinct from 'object'
     or (select array_agg(key order by key) from jsonb_object_keys(p_event->'move') key)
        is distinct from array['hops','promotion','start']::text[]
     or jsonb_typeof(p_event->'move'->'start') is distinct from 'array'
     or jsonb_typeof(p_event->'move'->'hops') is distinct from 'array'
     or jsonb_typeof(p_event->'move'->'promotion') not in ('string','null') then
    raise exception 'move intent must contain start, hops and promotion' using errcode = '22023';
  end if;
  if jsonb_array_length(p_event->'move'->'start') <> 2
     or jsonb_array_length(p_event->'move'->'hops') not between 1 and 128 then
    raise exception 'move coordinates and hop count are malformed' using errcode = '22023';
  end if;
  previous := null;
  for point in select value from jsonb_array_elements(
    jsonb_build_array(p_event->'move'->'start') || (p_event->'move'->'hops')
  ) loop
    if jsonb_typeof(point) is distinct from 'array' then
      raise exception 'move square must be an array' using errcode = '22023';
    end if;
    if jsonb_array_length(point) <> 2 or point = previous then
      raise exception 'move squares need two coordinates and distinct consecutive landings' using errcode = '22023';
    end if;
    perform bgwq.validate_session_square(point, game.config_snapshot->'board');
    previous := point;
  end loop;
  for point in select value from jsonb_array_elements(p_event->'captured') loop
    perform bgwq.validate_session_square(point, game.config_snapshot->'board');
  end loop;
  if p_event->'move'->'promotion' <> 'null'::jsonb and (
    char_length(p_event->'move'->>'promotion') not between 1 and 128
    or not (game.config_snapshot->'pieces' ? (p_event->'move'->>'promotion'))
  ) then
    raise exception 'promotion must name a configured piece' using errcode = '22023';
  end if;
  update bgwq.games set state = p_state, revision = revision + 1, updated_at = now() where id = p_game;
  insert into bgwq.events(game_id, revision, actor, payload, action_scope, action_id, state_hash)
  values (p_game, p_expected + 1, p_actor, p_event, 'domain', action, fingerprint);
  return p_expected + 1;
end $$;

alter table bgwq.games enable row level security;
alter table bgwq.events enable row level security;
revoke all on schema bgwq from public, anon, authenticated;
revoke all on bgwq.games, bgwq.events from public, anon, authenticated;
revoke all on all functions in schema bgwq from public, anon, authenticated;
alter default privileges in schema bgwq revoke execute on functions from public, anon, authenticated;
grant usage on schema bgwq to service_role;
grant select, insert, update on bgwq.games to service_role;
grant select, insert on bgwq.events to service_role;
grant execute on function bgwq.validate_session_square(jsonb,jsonb) to service_role;
grant execute on function bgwq.validate_session_snapshot(uuid,uuid,uuid,jsonb,bigint,jsonb) to service_role;
grant execute on function bgwq.create_game(uuid,uuid,text,jsonb) to service_role;
grant execute on function bgwq.activate_game(uuid,uuid,text,jsonb) to service_role;
grant execute on function bgwq.commit_revision(uuid,uuid,bigint,jsonb,jsonb) to service_role;
