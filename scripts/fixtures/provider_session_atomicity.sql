-- Execute against the reviewed private schema using an authorized administrator.
-- Real Supabase transaction/privilege probe; it does not authenticate users or prove game rules.
-- Existing Auth identities are referenced without alteration; every private test write rolls back.
begin;
do $probe$
declare
  identities uuid[];
  creator uuid;
  joiner uuid;
  outsider uuid;
  probe_game uuid := gen_random_uuid();
  create_key text;
  join_key text;
  fault_name text := 'provider_fault_' || replace(gen_random_uuid()::text, '-', '');
  state_zero jsonb := '{"version":1,"game_id":"00000000-0000-0000-0000-000000000010","config":{"schema_version":2,"name":"provider-transaction-fixture","title":"English Draughts","default":false,"playable":false,"board":{"rows":4,"columns":4,"starting_pieces":[{"piece":"man","color":"white","squares":[[3,0]]},{"piece":"man","color":"black","squares":[[0,3]]}]},"pieces":{"man":{"symbols":{"white":"⛀","black":"⛂"},"moves":[[-1,-1],[-1,1]],"attacks":[[1,1],[1,-1],[-1,1],[-1,-1]],"jump":false,"repeat":false,"notation":"","color_relative":true,"capture_policy":{"flying":false,"land_anywhere":false,"max_nodes":4096,"deferred_removal":false}},"king":{"symbols":{"white":"⛁","black":"⛃"},"moves":[[1,1],[1,-1],[-1,1],[-1,-1]],"attacks":[[1,1],[1,-1],[-1,1],[-1,-1]],"jump":false,"repeat":false,"notation":"","capture_policy":{"flying":false,"land_anywhere":false,"max_nodes":4096,"deferred_removal":false}}},"clock":{"initial_seconds":60,"increment_seconds":0},"exports":[],"appearance":{"light_square":"#E8DABC","dark_square":"#70573F"},"rules":[{"id":"permission","hook":"permits_move","when":{"op":"true"},"effects":[{"op":"permit","params":{}}]}],"quests":[]},"participants":{"1":"00000000-0000-0000-0000-000000000001","-1":"00000000-0000-0000-0000-000000000002"},"started_at_ms":1000,"active_side":1,"board":[{"square":[0,3],"kind":"man","side":-1,"moved":false},{"square":[3,0],"kind":"man","side":1,"moved":false}],"captured":[],"rule_state":{},"special_rights":{},"temporary_targets":{},"clocks":{"remaining_ms":{"1":60000,"-1":60000},"anchor_ms":1000,"increment_ms":0},"quest_progress":{"00000000-0000-0000-0000-000000000001":{},"00000000-0000-0000-0000-000000000002":{}},"outcome":null,"revision":0,"halfmove_count":0,"events":[],"position_history":["{\"active_side\":1,\"board\":[{\"kind\":\"man\",\"moved\":false,\"side\":-1,\"square\":[0,3]},{\"kind\":\"man\",\"moved\":false,\"side\":1,\"square\":[3,0]}],\"rights\":{},\"targets\":{}}"]}'::jsonb;
  state_one jsonb := '{"version":1,"game_id":"00000000-0000-0000-0000-000000000010","config":{"schema_version":2,"name":"provider-transaction-fixture","title":"English Draughts","default":false,"playable":false,"board":{"rows":4,"columns":4,"starting_pieces":[{"piece":"man","color":"white","squares":[[3,0]]},{"piece":"man","color":"black","squares":[[0,3]]}]},"pieces":{"man":{"symbols":{"white":"⛀","black":"⛂"},"moves":[[-1,-1],[-1,1]],"attacks":[[1,1],[1,-1],[-1,1],[-1,-1]],"jump":false,"repeat":false,"notation":"","color_relative":true,"capture_policy":{"flying":false,"land_anywhere":false,"max_nodes":4096,"deferred_removal":false}},"king":{"symbols":{"white":"⛁","black":"⛃"},"moves":[[1,1],[1,-1],[-1,1],[-1,-1]],"attacks":[[1,1],[1,-1],[-1,1],[-1,-1]],"jump":false,"repeat":false,"notation":"","capture_policy":{"flying":false,"land_anywhere":false,"max_nodes":4096,"deferred_removal":false}}},"clock":{"initial_seconds":60,"increment_seconds":0},"exports":[],"appearance":{"light_square":"#E8DABC","dark_square":"#70573F"},"rules":[{"id":"permission","hook":"permits_move","when":{"op":"true"},"effects":[{"op":"permit","params":{}}]}],"quests":[]},"participants":{"1":"00000000-0000-0000-0000-000000000001","-1":"00000000-0000-0000-0000-000000000002"},"started_at_ms":1000,"active_side":-1,"board":[{"square":[0,3],"kind":"man","side":-1,"moved":false},{"square":[2,1],"kind":"man","side":1,"moved":true}],"captured":[],"rule_state":{},"special_rights":{},"temporary_targets":{},"clocks":{"remaining_ms":{"1":59900,"-1":60000},"anchor_ms":1100,"increment_ms":0},"quest_progress":{"00000000-0000-0000-0000-000000000001":{},"00000000-0000-0000-0000-000000000002":{}},"outcome":null,"revision":1,"halfmove_count":1,"events":[{"revision":1,"expected_revision":0,"actor":"00000000-0000-0000-0000-000000000001","action_id":"create","at_ms":1100,"move":{"start":[3,0],"hops":[[2,1]],"promotion":null},"captured":[],"effects":[],"outcome":null}],"position_history":["{\"active_side\":1,\"board\":[{\"kind\":\"man\",\"moved\":false,\"side\":-1,\"square\":[0,3]},{\"kind\":\"man\",\"moved\":false,\"side\":1,\"square\":[3,0]}],\"rights\":{},\"targets\":{}}","{\"active_side\":-1,\"board\":[{\"kind\":\"man\",\"moved\":false,\"side\":-1,\"square\":[0,3]},{\"kind\":\"man\",\"moved\":true,\"side\":1,\"square\":[2,1]}],\"rights\":{},\"targets\":{}}"]}'::jsonb;
  state_two jsonb := '{"version":1,"game_id":"00000000-0000-0000-0000-000000000010","config":{"schema_version":2,"name":"provider-transaction-fixture","title":"English Draughts","default":false,"playable":false,"board":{"rows":4,"columns":4,"starting_pieces":[{"piece":"man","color":"white","squares":[[3,0]]},{"piece":"man","color":"black","squares":[[0,3]]}]},"pieces":{"man":{"symbols":{"white":"⛀","black":"⛂"},"moves":[[-1,-1],[-1,1]],"attacks":[[1,1],[1,-1],[-1,1],[-1,-1]],"jump":false,"repeat":false,"notation":"","color_relative":true,"capture_policy":{"flying":false,"land_anywhere":false,"max_nodes":4096,"deferred_removal":false}},"king":{"symbols":{"white":"⛁","black":"⛃"},"moves":[[1,1],[1,-1],[-1,1],[-1,-1]],"attacks":[[1,1],[1,-1],[-1,1],[-1,-1]],"jump":false,"repeat":false,"notation":"","capture_policy":{"flying":false,"land_anywhere":false,"max_nodes":4096,"deferred_removal":false}}},"clock":{"initial_seconds":60,"increment_seconds":0},"exports":[],"appearance":{"light_square":"#E8DABC","dark_square":"#70573F"},"rules":[{"id":"permission","hook":"permits_move","when":{"op":"true"},"effects":[{"op":"permit","params":{}}]}],"quests":[]},"participants":{"1":"00000000-0000-0000-0000-000000000001","-1":"00000000-0000-0000-0000-000000000002"},"started_at_ms":1000,"active_side":1,"board":[{"square":[1,2],"kind":"man","side":-1,"moved":true},{"square":[2,1],"kind":"man","side":1,"moved":true}],"captured":[],"rule_state":{},"special_rights":{},"temporary_targets":{},"clocks":{"remaining_ms":{"1":59900,"-1":59900},"anchor_ms":1200,"increment_ms":0},"quest_progress":{"00000000-0000-0000-0000-000000000001":{},"00000000-0000-0000-0000-000000000002":{}},"outcome":null,"revision":2,"halfmove_count":2,"events":[{"revision":1,"expected_revision":0,"actor":"00000000-0000-0000-0000-000000000001","action_id":"create","at_ms":1100,"move":{"start":[3,0],"hops":[[2,1]],"promotion":null},"captured":[],"effects":[],"outcome":null},{"revision":2,"expected_revision":1,"actor":"00000000-0000-0000-0000-000000000002","action_id":"join","at_ms":1200,"move":{"start":[0,3],"hops":[[1,2]],"promotion":null},"captured":[],"effects":[],"outcome":null}],"position_history":["{\"active_side\":1,\"board\":[{\"kind\":\"man\",\"moved\":false,\"side\":-1,\"square\":[0,3]},{\"kind\":\"man\",\"moved\":false,\"side\":1,\"square\":[3,0]}],\"rights\":{},\"targets\":{}}","{\"active_side\":-1,\"board\":[{\"kind\":\"man\",\"moved\":false,\"side\":-1,\"square\":[0,3]},{\"kind\":\"man\",\"moved\":true,\"side\":1,\"square\":[2,1]}],\"rights\":{},\"targets\":{}}","{\"active_side\":1,\"board\":[{\"kind\":\"man\",\"moved\":true,\"side\":-1,\"square\":[1,2]},{\"kind\":\"man\",\"moved\":true,\"side\":1,\"square\":[2,1]}],\"rights\":{},\"targets\":{}}"]}'::jsonb;
  first_event jsonb;
  second_event jsonb;
  original jsonb;
  modified jsonb;
  rejected boolean;
  actor_role text;
  config jsonb;
  result bigint;
begin
  select array_agg(id order by id) into identities from (select id from auth.users order by id limit 3) users;
  if coalesce(array_length(identities, 1),0) < 3 then
    raise exception 'provider verification blocked: three existing Auth identities are required';
  end if;
  creator := identities[1]; joiner := identities[2]; outsider := identities[3];
  create_key := 'probe-create-' || probe_game::text;
  join_key := 'probe-join-' || probe_game::text;
  state_zero := state_zero || jsonb_build_object(
    'game_id', probe_game::text,
    'participants', jsonb_build_object('1',creator::text,'-1',joiner::text),
    'quest_progress', jsonb_build_object(creator::text,'{}'::jsonb,joiner::text,'{}'::jsonb));
  state_one := state_one || jsonb_build_object('game_id',probe_game::text,
    'participants',state_zero->'participants','quest_progress',state_zero->'quest_progress');
  state_two := state_two || jsonb_build_object('game_id',probe_game::text,
    'participants',state_zero->'participants','quest_progress',state_zero->'quest_progress');
  first_event := (state_one->'events'->0) || jsonb_build_object('actor',creator::text,'action_id',create_key);
  second_event := (state_two->'events'->1) || jsonb_build_object('actor',joiner::text,'action_id',join_key);
  state_one := jsonb_set(state_one,'{events}',jsonb_build_array(first_event));
  state_two := jsonb_set(state_two,'{events}',jsonb_build_array(first_event,second_event));
  config := state_zero->'config';

  if has_table_privilege('service_role','auth.users','SELECT') then
    raise exception 'service role must not gain Auth record SELECT access';
  end if;
  foreach actor_role in array array['anon','authenticated'] loop
    if has_schema_privilege(actor_role,'bgwq','USAGE')
       or has_table_privilege(actor_role,'bgwq.games','SELECT')
       or has_table_privilege(actor_role,'bgwq.events','SELECT')
       or has_function_privilege(actor_role,'bgwq.create_game(uuid,uuid,text,jsonb)','EXECUTE')
       or has_function_privilege(actor_role,'bgwq.activate_game(uuid,uuid,text,jsonb)','EXECUTE')
       or has_function_privilege(actor_role,'bgwq.commit_revision(uuid,uuid,bigint,jsonb,jsonb)','EXECUTE') then
      raise exception 'browser role exposes the private persistence boundary';
    end if;
  end loop;
  if not (select bool_and(relrowsecurity) from pg_class where oid in ('bgwq.games'::regclass,'bgwq.events'::regclass))
     or exists (select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='bgwq' and p.prosecdef) then
    raise exception 'private persistence requires RLS and invoker functions';
  end if;

  execute 'set local role service_role';
  if bgwq.create_game(probe_game,creator,create_key,config) <> probe_game
     or bgwq.create_game(probe_game,creator,create_key,config) <> probe_game then
    raise exception 'creation exact retry did not return the stable game';
  end if;
  select to_jsonb(g) into original from bgwq.games g where id=probe_game;
  rejected := false;
  begin perform bgwq.create_game(probe_game,creator,create_key,config || '{"title":"conflict"}'::jsonb);
  exception when sqlstate '23505' then rejected := true; end;
  if not rejected or (select to_jsonb(g) from bgwq.games g where id=probe_game) <> original then
    raise exception 'creation key collision mutated the pending game';
  end if;
  rejected := false;
  begin perform bgwq.create_game(gen_random_uuid(),creator,'bad','{"schema_version":true}'::jsonb);
  exception when sqlstate '22023' then rejected := true; end;
  if not rejected then raise exception 'malformed creation accepted'; end if;

  modified := jsonb_set(state_zero,'{revision}','false'::jsonb);
  rejected := false;
  begin perform bgwq.activate_game(probe_game,joiner,join_key,modified);
  exception when sqlstate '22023' then rejected := true; end;
  if not rejected or (select to_jsonb(g) from bgwq.games g where id=probe_game) <> original then
    raise exception 'malformed activation mutated the pending slot';
  end if;
  if bgwq.activate_game(probe_game,joiner,join_key,state_zero) <> 0 then
    raise exception 'activation did not preserve domain revision zero';
  end if;
  if (select count(*) from bgwq.events where game_id=probe_game) < 1 then
    raise exception 'activation event was not durable';
  end if;
  select to_jsonb(g) into original from bgwq.games g where id=probe_game;
  if bgwq.activate_game(probe_game,joiner,join_key,state_zero) <> 0 then raise exception 'activation exact retry failed'; end if;
  rejected := false;
  begin perform bgwq.activate_game(probe_game,outsider,'third',state_zero);
  exception when sqlstate '55000' then rejected := true; end;
  if not rejected or (select to_jsonb(g) from bgwq.games g where id=probe_game) <> original then
    raise exception 'third participant changed immutable membership';
  end if;
  rejected := false;
  begin update bgwq.games set player_two=outsider where id=probe_game;
  exception when sqlstate '23514' then rejected := true; end;
  if not rejected then raise exception 'active participants were mutable'; end if;

  rejected := false;
  begin perform bgwq.commit_revision(probe_game,outsider,0,state_one,first_event);
  exception when sqlstate '42501' then rejected := true; end;
  if not rejected then raise exception 'outsider committed'; end if;
  rejected := false;
  begin perform bgwq.commit_revision(probe_game,joiner,0,state_one,first_event);
  exception when sqlstate '42501' then rejected := true; end;
  if not rejected then raise exception 'wrong-turn participant committed'; end if;
  modified := jsonb_set(state_one,'{participants,1}',to_jsonb(outsider::text));
  rejected := false;
  begin perform bgwq.commit_revision(probe_game,creator,0,modified,first_event);
  exception when sqlstate '22023' then rejected := true; end;
  if not rejected or (select to_jsonb(g) from bgwq.games g where id=probe_game) <> original then
    raise exception 'invalid submissions changed authoritative state';
  end if;

  -- A trigger fault tests rollback after the game-row update, before event insertion.
  execute 'reset role';
  execute format('create function bgwq.%I() returns trigger language plpgsql as $fault$begin if new.game_id=%L::uuid and new.revision=1 then raise exception ''injected event failure''; end if; return new; end;$fault$',fault_name,probe_game);
  execute format('create trigger %I before insert on bgwq.events for each row execute function bgwq.%I()',fault_name,fault_name);
  execute 'set local role service_role';
  rejected := false;
  begin perform bgwq.commit_revision(probe_game,creator,0,state_one,first_event);
  exception when sqlstate 'P0001' then rejected := true; end;
  if not rejected or (select to_jsonb(g) from bgwq.games g where id=probe_game) <> original then
    raise exception 'failed event insertion did not roll back state';
  end if;
  execute 'reset role';
  execute format('drop trigger %I on bgwq.events',fault_name);
  execute format('drop function bgwq.%I()',fault_name);
  execute 'set local role service_role';

  -- Creation, activation and domain action namespaces permit equal textual keys.
  if bgwq.commit_revision(probe_game,creator,0,state_one,first_event) <> 1
     or bgwq.commit_revision(probe_game,creator,0,state_one,first_event) <> 1
     or bgwq.commit_revision(probe_game,joiner,1,state_two,second_event) <> 2 then
    raise exception 'commit or idempotent revision result was incorrect';
  end if;
  select to_jsonb(g) into original from bgwq.games g where id=probe_game;
  if bgwq.commit_revision(probe_game,creator,0,state_one,first_event) <> 1
     or bgwq.activate_game(probe_game,joiner,join_key,state_zero) <> 0 then
    raise exception 'historical exact retries failed after later commits';
  end if;
  modified := jsonb_set(state_one,'{halfmove_count}','2'::jsonb);
  rejected := false;
  begin perform bgwq.commit_revision(probe_game,creator,0,modified,first_event);
  exception when sqlstate '23505' then rejected := true; end;
  if not rejected then raise exception 'conflicting domain retry accepted'; end if;
  rejected := false;
  begin perform bgwq.commit_revision(probe_game,creator,0,state_one,first_event || '{"action_id":"stale"}'::jsonb);
  exception when sqlstate '40001' then rejected := true; end;
  if not rejected or (select to_jsonb(g) from bgwq.games g where id=probe_game) <> original then
    raise exception 'stale action changed the durable state';
  end if;
  if (select count(*) from bgwq.events e where e.game_id=probe_game) <> 3
     or (select state->'events' from bgwq.games where id=probe_game) <> state_two->'events' then
    raise exception 'activation/domain transcript mismatch';
  end if;
  execute 'reset role';
end $probe$;
rollback;
select 'private Supabase lifecycle, retry, authorization and rollback probe passed' as verification;
