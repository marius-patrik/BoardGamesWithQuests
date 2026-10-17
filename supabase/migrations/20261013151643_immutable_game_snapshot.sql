-- Prevent any change to a running game's immutable identity and JSON config.
create or replace function bgwq.prevent_snapshot_mutation()
returns trigger language plpgsql security invoker set search_path='' as $$
begin
  if new.id is distinct from old.id
     or new.player_one is distinct from old.player_one
     or new.player_two is distinct from old.player_two
     or new.config_snapshot is distinct from old.config_snapshot
     or new.created_at is distinct from old.created_at then
    raise exception 'running game identity and configuration are immutable'
      using errcode='23514';
  end if;
  return new;
end $$;
revoke all on function bgwq.prevent_snapshot_mutation() from public,anon,authenticated;
drop trigger if exists bgwq_protect_game_snapshot on bgwq.games;
create trigger bgwq_protect_game_snapshot
before update on bgwq.games
for each row execute function bgwq.prevent_snapshot_mutation();
