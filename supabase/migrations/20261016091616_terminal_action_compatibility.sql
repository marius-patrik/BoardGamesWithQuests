-- Bounded terminal envelopes; engine-owned legality and outcome evaluation.
create or replace function bgwq.commit_revision(
  p_game uuid, p_actor uuid, p_expected bigint, p_state jsonb, p_event jsonb
) returns bigint language plpgsql security invoker set search_path = '' as $$
declare game bgwq.games%rowtype; existing bgwq.events%rowtype; action text; fingerprint bytea; side text; point jsonb; previous jsonb; terminal boolean; command text; intent jsonb; field text; elapsed numeric; remaining numeric; result jsonb;
begin
  if p_game is null or p_actor is null or p_expected is null or p_expected < 0 or p_expected >= 4096
     or jsonb_typeof(p_state) is distinct from 'object'
     or jsonb_typeof(p_event) is distinct from 'object'
     or jsonb_typeof(p_event->'action_id') is distinct from 'string'
     or char_length(p_event->>'action_id') not between 1 and 128 then
    raise exception 'invalid commit arguments' using errcode = '22023';
  end if;
  terminal := p_event ? 'action';
  command := p_event->'action'->>'type';
  if (select array_agg(key order by key) from jsonb_object_keys(p_event) key)
       is distinct from (case when terminal then array['action','action_id','actor','at_ms','captured','effects','expected_revision','move','outcome','revision'] else array['action_id','actor','at_ms','captured','effects','expected_revision','move','outcome','revision'] end)::text[]
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
  if (not terminal or command = 'claim_draw') and p_actor <> (case side when '1' then game.player_one else game.player_two end) then
    raise exception 'actor does not control the active turn' using errcode = '42501';
  end if;
  if game.state->'outcome' <> 'null'::jsonb then
    raise exception 'game has a terminal outcome' using errcode = '55000';
  end if;
  perform bgwq.validate_session_snapshot(p_game, game.player_one, game.player_two, game.config_snapshot, p_expected + 1, p_state);
  if p_state->>'active_side' is distinct from (case when terminal then side else (-(side::integer))::text end)
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
  if terminal then
    if jsonb_typeof(p_event->'action') is distinct from 'object' then
      raise exception 'terminal action must be an object' using errcode = '22023';
    end if;
    if command is null or command not in ('resign','claim_draw','timeout')
       or (select array_agg(key order by key) from jsonb_object_keys(p_event->'action') key)
         is distinct from (case when command = 'claim_draw' then array['claim','intended_move','type'] else array['type'] end)
       or p_event->'move' is distinct from 'null'::jsonb
       or p_event->'captured' is distinct from '[]'::jsonb
       or p_event->'effects' is distinct from '[]'::jsonb then
      raise exception 'invalid canonical terminal action' using errcode = '22023';
    end if;
    foreach field in array array['board','captured','rule_state','special_rights','temporary_targets','quest_progress','halfmove_count','position_history'] loop
      if p_state->field is distinct from game.state->field then
        raise exception 'terminal action mutates %', field using errcode = '22023';
      end if;
    end loop;
    elapsed := (p_event->>'at_ms')::numeric - (game.state->'clocks'->>'anchor_ms')::numeric;
    remaining := (game.state->'clocks'->'remaining_ms'->>side)::numeric;
    if (command = 'timeout' and elapsed < remaining)
       or (command = 'claim_draw' and elapsed >= remaining)
       or p_state->'clocks'->'remaining_ms'->side is distinct from to_jsonb(greatest(0, remaining - elapsed))
       or p_state->'clocks'->'remaining_ms'->((-(side::integer))::text) is distinct from game.state->'clocks'->'remaining_ms'->((-(side::integer))::text) then
      raise exception 'terminal clock or deadline assertion is invalid' using errcode = '22023';
    end if;
    result := p_state->'outcome';
    if jsonb_typeof(result) is distinct from 'object' then
      raise exception 'terminal result is required' using errcode = '22023';
    end if;
    if (select array_agg(key order by key) from jsonb_object_keys(result) key) is distinct from array['cause','kind','priority','winner']
       or jsonb_typeof(result->'kind') is distinct from 'string' or result->>'kind' = ''
       or jsonb_typeof(result->'cause') is distinct from 'string' or result->>'cause' = ''
       or jsonb_typeof(result->'priority') is distinct from 'number'
       or result->>'priority' !~ '^-?(0|[1-9][0-9]*)$'
       or (result->>'priority')::numeric not between -1000 and 1000
       or (result->'winner' <> 'null'::jsonb and result->>'winner' not in (game.player_one::text,game.player_two::text))
       or (command = 'claim_draw' and (result->>'kind' <> 'draw' or result->'winner' <> 'null'::jsonb)) then
      raise exception 'invalid terminal result' using errcode = '22023';
    end if;
    -- SQL checks configured proposal metadata; only the engine evaluates predicates,
    -- expression references, projected claims and priority arbitration.
    if not exists (
      select 1 from jsonb_array_elements(game.config_snapshot->'rules') r,
        lateral jsonb_array_elements(r->'effects') e
      where r->>'hook' = 'outcome' and e->>'op' = 'propose_outcome'
        and (jsonb_typeof(e->'params'->'kind') = 'object' or e->'params'->'kind' = result->'kind')
        and (jsonb_typeof(e->'params'->'cause') = 'object' or e->'params'->'cause' = result->'cause')
        and (jsonb_typeof(e->'params'->'priority') = 'object' or e->'params'->'priority' = result->'priority')
        and ((jsonb_typeof(e->'params'->'winner') = 'object'
            and case e->'params'->'winner'->>'ref'
              when 'player.opponent.id' then result->>'winner' = (case when p_actor = game.player_one then game.player_two else game.player_one end)::text
              when 'player.id' then result->>'winner' = p_actor::text
              when 'event.actor' then result->>'winner' = p_actor::text
              else true end)
          or e->'params'->'winner' = result->'winner'
          or (e->'params'->>'winner' in ('1','-1') and game.state->'participants'->(e->'params'->>'winner') = result->'winner'))
    ) then
      raise exception 'result has no configured proposal' using errcode = '22023';
    end if;
    if command = 'claim_draw' then
      if jsonb_typeof(p_event->'action'->'claim') is distinct from 'string'
         or octet_length(p_event->'action'->>'claim') not between 1 and 262144
         or not exists (select 1 from jsonb_array_elements(game.config_snapshot->'rules') r
           where r->>'hook' = 'outcome' and r->>'id' = p_event->'action'->>'claim') then
        raise exception 'claim must name a configured outcome rule' using errcode = '22023';
      end if;
    end if;
    intent := p_event->'action'->'intended_move';
  else
    intent := p_event->'move';
  end if;
  if not terminal or (command = 'claim_draw' and intent <> 'null'::jsonb) then
    if jsonb_typeof(intent) is distinct from 'object'
       or (select array_agg(key order by key) from jsonb_object_keys(intent) key)
          is distinct from array['hops','promotion','start']::text[]
       or jsonb_typeof(intent->'start') is distinct from 'array'
       or jsonb_typeof(intent->'hops') is distinct from 'array'
       or jsonb_typeof(intent->'promotion') not in ('string','null') then
      raise exception 'move intent must contain start, hops and promotion' using errcode = '22023';
    end if;
    if jsonb_array_length(intent->'start') <> 2
       or jsonb_array_length(intent->'hops') not between 1 and 128 then
      raise exception 'move coordinates and hop count are malformed' using errcode = '22023';
    end if;
    previous := null;
    for point in select value from jsonb_array_elements(
      jsonb_build_array(intent->'start') || (intent->'hops')
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
    if intent->'promotion' <> 'null'::jsonb and (
      char_length(intent->>'promotion') not between 1 and 128
      or not (game.config_snapshot->'pieces' ? (intent->>'promotion'))
    ) then
      raise exception 'promotion must name a configured piece' using errcode = '22023';
    end if;
  end if;
  update bgwq.games set state = p_state, revision = revision + 1, updated_at = now() where id = p_game;
  insert into bgwq.events(game_id, revision, actor, payload, action_scope, action_id, state_hash)
  values (p_game, p_expected + 1, p_actor, p_event, 'domain', action, fingerprint);
  return p_expected + 1;
end $$;
