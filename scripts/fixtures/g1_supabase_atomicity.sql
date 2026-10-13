-- Re-run against the dedicated private bgwq schema through an authorized
-- Supabase database connection. This probe creates and removes its test row.
-- It verifies only the transactional revision boundary, not move legality.
do $$
declare
  gid uuid := gen_random_uuid();
  first_player uuid := gen_random_uuid();
  second_player uuid := gen_random_uuid();
  stranger uuid := gen_random_uuid();
  new_revision bigint;
  invalid_actor_rejected boolean := false;
  stale_revision_rejected boolean := false;
  event_count integer;
begin
  insert into bgwq.games(id, player_one, player_two, config_snapshot, state)
  values(
    gid, first_player, second_player,
    '{"schema_version":2}'::jsonb,
    '{"turn":1}'::jsonb
  );
  new_revision := bgwq.commit_revision(
    gid, first_player, 0, '{"turn":-1}'::jsonb, '{"move":"valid"}'::jsonb
  );
  if new_revision <> 1 then
    raise exception 'revision was not advanced exactly once';
  end if;

  begin
    perform bgwq.commit_revision(
      gid, stranger, 1, '{"turn":1}'::jsonb, '{"move":"intruder"}'::jsonb
    );
  exception when sqlstate '40001' then
    invalid_actor_rejected := true;
  end;

  begin
    perform bgwq.commit_revision(
      gid, second_player, 0, '{"turn":1}'::jsonb, '{"move":"stale"}'::jsonb
    );
  exception when sqlstate '40001' then
    stale_revision_rejected := true;
  end;

  if not invalid_actor_rejected or not stale_revision_rejected then
    raise exception 'authorization or revision check failed open';
  end if;
  select count(*) into event_count from bgwq.events where game_id = gid;
  if event_count <> 1 then
    raise exception 'failed submissions produced side effects';
  end if;
  if not exists(
    select 1 from bgwq.games
    where id=gid and revision=1 and state='{"turn":-1}'::jsonb
  ) then
    raise exception 'failed submissions modified authoritative state';
  end if;
  delete from bgwq.games where id=gid;
end
$$;

-- These three values must be false; both tables must report RLS enabled.
select
  has_schema_privilege('authenticated','bgwq','USAGE') as public_schema_usage,
  has_table_privilege('authenticated','bgwq.games','SELECT') as public_read,
  has_function_privilege(
    'authenticated',
    'bgwq.commit_revision(uuid,uuid,bigint,jsonb,jsonb)',
    'EXECUTE'
  ) as public_commit;
