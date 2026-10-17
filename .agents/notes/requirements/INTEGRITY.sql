-- BoardGamesWithQuests supplemental PostgreSQL declarations.
-- SCHEMA.prisma is authoritative for tables, enums, indexes and intra-bgwq FKs.
-- This file defines features Prisma schema language cannot safely model:
-- CHECK constraints, partial unique indexes, Supabase-managed auth.users FKs,
-- private Broadcast policies, publication immutability and revision/event parity.
-- Reapply after Prisma Migrate; DO blocks are idempotent.
-- Changes to these contracts must be reviewed alongside SCHEMA.prisma.

-- definition_builtin_ownership: definitions schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'definition_builtin_ownership' AND conrelid = 'bgwq.definitions'::regclass) THEN
    ALTER TABLE bgwq."definitions" ADD CONSTRAINT "definition_builtin_ownership" CHECK ("built_in" = ("owner_id" IS NULL));
  END IF;
END $bgwq_check$;
-- definition_owner_key: filtered index not expressible without Prisma preview features.
CREATE UNIQUE INDEX IF NOT EXISTS "definition_owner_key" ON bgwq."definitions" ("owner_id", "key") WHERE "owner_id" IS NOT NULL;
-- builtin_definition_key: filtered index not expressible without Prisma preview features.
CREATE UNIQUE INDEX IF NOT EXISTS "builtin_definition_key" ON bgwq."definitions" ("key") WHERE "built_in";
-- version_bounds: versions schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'version_bounds' AND conrelid = 'bgwq.versions'::regclass) THEN
    ALTER TABLE bgwq."versions" ADD CONSTRAINT "version_bounds" CHECK ("minimum_participants">0 AND "maximum_participants">="minimum_participants");
  END IF;
END $bgwq_check$;
-- role_count: roles schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'role_count' AND conrelid = 'bgwq.roles'::regclass) THEN
    ALTER TABLE bgwq."roles" ADD CONSTRAINT "role_count" CHECK ("minimum_count">=0 AND "maximum_count">="minimum_count");
  END IF;
END $bgwq_check$;
-- role_forward_row: roles schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'role_forward_row' AND conrelid = 'bgwq.roles'::regclass) THEN
    ALTER TABLE bgwq."roles" ADD CONSTRAINT "role_forward_row" CHECK ("forward_row" IS NULL OR "forward_row" IN (-1,1));
  END IF;
END $bgwq_check$;
-- phase_single_initial: filtered index not expressible without Prisma preview features.
CREATE UNIQUE INDEX IF NOT EXISTS "phase_single_initial" ON bgwq."phases" ("version_id") WHERE "initial";
-- seed_not_self: entity_seeds schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'seed_not_self' AND conrelid = 'bgwq.entity_seeds'::regclass) THEN
    ALTER TABLE bgwq."entity_seeds" ADD CONSTRAINT "seed_not_self" CHECK ("parent_id" IS DISTINCT FROM "id" AND "location_id" IS DISTINCT FROM "id");
  END IF;
END $bgwq_check$;
-- seed_value_one_payload: seed_values schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'seed_value_one_payload' AND conrelid = 'bgwq.seed_values'::regclass) THEN
    ALTER TABLE bgwq."seed_values" ADD CONSTRAINT "seed_value_one_payload" CHECK (("kind"='none' AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_seed_id","ref_seat")=0) OR ("kind"='bool' AND "bool_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_seed_id","ref_seat")=1) OR ("kind"='int' AND "int_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_seed_id","ref_seat")=1) OR ("kind"='decimal' AND "decimal_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_seed_id","ref_seat")=1) OR ("kind"='text' AND "text_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_seed_id","ref_seat")=1) OR ("kind"='instant' AND "instant_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_seed_id","ref_seat")=1) OR ("kind"='entity' AND "ref_seed_id" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_seed_id","ref_seat")=1) OR ("kind"='participant' AND "ref_seat" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_seed_id","ref_seat")=1));
  END IF;
END $bgwq_check$;
-- operator_kind: operators schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'operator_kind' AND conrelid = 'bgwq.operators'::regclass) THEN
    ALTER TABLE bgwq."operators" ADD CONSTRAINT "operator_kind" CHECK ("kind" IN ('expression','effect'));
  END IF;
END $bgwq_check$;
-- expression_kind: expressions schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'expression_kind' AND conrelid = 'bgwq.expressions'::regclass) THEN
    ALTER TABLE bgwq."expressions" ADD CONSTRAINT "expression_kind" CHECK ("kind" IN ('literal','context','field','local','call'));
  END IF;
END $bgwq_check$;
-- expression_not_self: expression_arguments schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'expression_not_self' AND conrelid = 'bgwq.expression_arguments'::regclass) THEN
    ALTER TABLE bgwq."expression_arguments" ADD CONSTRAINT "expression_not_self" CHECK ("parent_id"<>"child_id");
  END IF;
END $bgwq_check$;
-- action_trigger_check: actions schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'action_trigger_check' AND conrelid = 'bgwq.actions'::regclass) THEN
    ALTER TABLE bgwq."actions" ADD CONSTRAINT "action_trigger_check" CHECK (("trigger"='command' AND "hook_key" IS NULL) OR ("trigger"='hook' AND "hook_key" IS NOT NULL));
  END IF;
END $bgwq_check$;
-- action_iterator_pair: actions schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'action_iterator_pair' AND conrelid = 'bgwq.actions'::regclass) THEN
    ALTER TABLE bgwq."actions" ADD CONSTRAINT "action_iterator_pair" CHECK (("iterator_expression_id" IS NULL) = ("iterator_var" IS NULL));
  END IF;
END $bgwq_check$;
-- asset_size: assets schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'asset_size' AND conrelid = 'bgwq.assets'::regclass) THEN
    ALTER TABLE bgwq."assets" ADD CONSTRAINT "asset_size" CHECK ("bytes" BETWEEN 1 AND 2097152);
  END IF;
END $bgwq_check$;
-- asset_hash_lower_hex: assets schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'asset_hash_lower_hex' AND conrelid = 'bgwq.assets'::regclass) THEN
    ALTER TABLE bgwq."assets" ADD CONSTRAINT "asset_hash_lower_hex" CHECK ("sha256" ~ '^[0-9a-f]{64}$');
  END IF;
END $bgwq_check$;
-- asset_supported_mime: assets schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'asset_supported_mime' AND conrelid = 'bgwq.assets'::regclass) THEN
    ALTER TABLE bgwq."assets" ADD CONSTRAINT "asset_supported_mime" CHECK ("mime" IN ('image/png','image/webp'));
  END IF;
END $bgwq_check$;
-- asset_path_nonempty: assets schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'asset_path_nonempty' AND conrelid = 'bgwq.assets'::regclass) THEN
    ALTER TABLE bgwq."assets" ADD CONSTRAINT "asset_path_nonempty" CHECK (length(btrim("path"))>0);
  END IF;
END $bgwq_check$;
-- visual_primitive_kind: visual_primitives schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'visual_primitive_kind' AND conrelid = 'bgwq.visual_primitives'::regclass) THEN
    ALTER TABLE bgwq."visual_primitives" ADD CONSTRAINT "visual_primitive_kind" CHECK ("kind" IN ('rectangle','ellipse','line','path','text','image'));
  END IF;
END $bgwq_check$;
-- game_revision_nonnegative: games schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'game_revision_nonnegative' AND conrelid = 'bgwq.games'::regclass) THEN
    ALTER TABLE bgwq."games" ADD CONSTRAINT "game_revision_nonnegative" CHECK ("revision">=0 AND "turn">=0);
  END IF;
END $bgwq_check$;
-- game_lifecycle_timestamps: games schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'game_lifecycle_timestamps' AND conrelid = 'bgwq.games'::regclass) THEN
    ALTER TABLE bgwq."games" ADD CONSTRAINT "game_lifecycle_timestamps" CHECK (("status"='pending' AND "started_at" IS NULL AND "finished_at" IS NULL) OR ("status"='expired' AND "started_at" IS NULL AND "finished_at" IS NULL) OR ("status"='active' AND "started_at" IS NOT NULL AND "finished_at" IS NULL) OR ("status"='finished' AND "started_at" IS NOT NULL AND "finished_at" IS NOT NULL));
  END IF;
END $bgwq_check$;
-- participant_seat_nonnegative: participants schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'participant_seat_nonnegative' AND conrelid = 'bgwq.participants'::regclass) THEN
    ALTER TABLE bgwq."participants" ADD CONSTRAINT "participant_seat_nonnegative" CHECK ("seat">=0);
  END IF;
END $bgwq_check$;
-- runtime_entity_self: game_entities schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'runtime_entity_self' AND conrelid = 'bgwq.game_entities'::regclass) THEN
    ALTER TABLE bgwq."game_entities" ADD CONSTRAINT "runtime_entity_self" CHECK ("id" IS DISTINCT FROM "parent_id" AND "id" IS DISTINCT FROM "location_id");
  END IF;
END $bgwq_check$;
-- game_value_exactly_one: game_values schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'game_value_exactly_one' AND conrelid = 'bgwq.game_values'::regclass) THEN
    ALTER TABLE bgwq."game_values" ADD CONSTRAINT "game_value_exactly_one" CHECK (("kind"='none' AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id")=0) OR ("kind"='bool' AND "bool_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id")=1) OR ("kind"='int' AND "int_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id")=1) OR ("kind"='decimal' AND "decimal_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id")=1) OR ("kind"='text' AND "text_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id")=1) OR ("kind"='instant' AND "instant_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id")=1) OR ("kind"='entity' AND "ref_entity_id" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id")=1) OR ("kind"='participant' AND "ref_participant_id" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id")=1));
  END IF;
END $bgwq_check$;
-- game_composite_kind: game_composites schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'game_composite_kind' AND conrelid = 'bgwq.game_composites'::regclass) THEN
    ALTER TABLE bgwq."game_composites" ADD CONSTRAINT "game_composite_kind" CHECK ("container_kind" IN ('list','record'));
  END IF;
END $bgwq_check$;
-- game_composite_entry_index: game_composite_entries schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'game_composite_entry_index' AND conrelid = 'bgwq.game_composite_entries'::regclass) THEN
    ALTER TABLE bgwq."game_composite_entries" ADD CONSTRAINT "game_composite_entry_index" CHECK ("ordinal">=0);
  END IF;
END $bgwq_check$;
-- game_composite_entry_value: game_composite_entries schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'game_composite_entry_value' AND conrelid = 'bgwq.game_composite_entries'::regclass) THEN
    ALTER TABLE bgwq."game_composite_entries" ADD CONSTRAINT "game_composite_entry_value" CHECK (("kind" IS NULL AND "child_composite_id" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id","child_composite_id")=1) OR ("kind"='bool' AND "bool_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id","child_composite_id")=1) OR ("kind"='int' AND "int_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id","child_composite_id")=1) OR ("kind"='decimal' AND "decimal_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id","child_composite_id")=1) OR ("kind"='text' AND "text_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id","child_composite_id")=1) OR ("kind"='instant' AND "instant_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id","child_composite_id")=1) OR ("kind"='entity' AND "ref_entity_id" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id","child_composite_id")=1) OR ("kind"='participant' AND "ref_participant_id" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","ref_entity_id","ref_participant_id","child_composite_id")=1));
  END IF;
END $bgwq_check$;
-- game_composite_no_self: game_composite_entries schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'game_composite_no_self' AND conrelid = 'bgwq.game_composite_entries'::regclass) THEN
    ALTER TABLE bgwq."game_composite_entries" ADD CONSTRAINT "game_composite_no_self" CHECK ("composite_id" IS DISTINCT FROM "child_composite_id");
  END IF;
END $bgwq_check$;
-- clock_nonnegative: clocks schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'clock_nonnegative' AND conrelid = 'bgwq.clocks'::regclass) THEN
    ALTER TABLE bgwq."clocks" ADD CONSTRAINT "clock_nonnegative" CHECK ("remaining_ms">=0 AND "increment_ms">=0);
  END IF;
END $bgwq_check$;
-- event_value_one_payload: event_values schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'event_value_one_payload' AND conrelid = 'bgwq.event_values'::regclass) THEN
    ALTER TABLE bgwq."event_values" ADD CONSTRAINT "event_value_one_payload" CHECK (("kind"='none' AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","entity_id","participant_id")=0) OR ("kind"='bool' AND "bool_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","entity_id","participant_id")=1) OR ("kind"='int' AND "int_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","entity_id","participant_id")=1) OR ("kind"='decimal' AND "decimal_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","entity_id","participant_id")=1) OR ("kind"='text' AND "text_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","entity_id","participant_id")=1) OR ("kind"='instant' AND "instant_value" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","entity_id","participant_id")=1) OR ("kind"='entity' AND "entity_id" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","entity_id","participant_id")=1) OR ("kind"='participant' AND "participant_id" IS NOT NULL AND num_nonnulls("bool_value","int_value","decimal_value","text_value","instant_value","entity_id","participant_id")=1));
  END IF;
END $bgwq_check$;
-- mutation_target_kind: event_mutations schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'mutation_target_kind' AND conrelid = 'bgwq.event_mutations'::regclass) THEN
    ALTER TABLE bgwq."event_mutations" ADD CONSTRAINT "mutation_target_kind" CHECK ("target_kind" IN ('entity','link','field','phase','active_participant','clock','award','game'));
  END IF;
END $bgwq_check$;
-- award_points: awards schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'award_points' AND conrelid = 'bgwq.awards'::regclass) THEN
    ALTER TABLE bgwq."awards" ADD CONSTRAINT "award_points" CHECK ("points">=0);
  END IF;
END $bgwq_check$;
-- rating_counts: ratings schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'rating_counts' AND conrelid = 'bgwq.ratings'::regclass) THEN
    ALTER TABLE bgwq."ratings" ADD CONSTRAINT "rating_counts" CHECK ("games"="wins"+"draws"+"losses");
  END IF;
END $bgwq_check$;
-- rating_nonnegative: ratings schema-level invariant.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'rating_nonnegative' AND conrelid = 'bgwq.ratings'::regclass) THEN
    ALTER TABLE bgwq."ratings" ADD CONSTRAINT "rating_nonnegative" CHECK ("games">=0 AND "wins">=0 AND "draws">=0 AND "losses">=0 AND "rating">=0);
  END IF;
END $bgwq_check$;

-- A mutation's before/after payload is typed. Structural inserts/removals use
-- absent before/after respectively; scalar references remain UUIDs in the log.
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'mutation_typed_before' AND conrelid = 'bgwq.event_mutations'::regclass) THEN
    ALTER TABLE bgwq.event_mutations ADD CONSTRAINT mutation_typed_before CHECK (
      (before_kind IS NULL AND num_nonnulls(before_bool,before_int,before_decimal,before_text,before_instant,before_ref)=0)
      OR (before_kind='none' AND num_nonnulls(before_bool,before_int,before_decimal,before_text,before_instant,before_ref)=0)
      OR (before_kind='bool' AND before_bool IS NOT NULL AND num_nonnulls(before_bool,before_int,before_decimal,before_text,before_instant,before_ref)=1)
      OR (before_kind='int' AND before_int IS NOT NULL AND num_nonnulls(before_bool,before_int,before_decimal,before_text,before_instant,before_ref)=1)
      OR (before_kind='decimal' AND before_decimal IS NOT NULL AND num_nonnulls(before_bool,before_int,before_decimal,before_text,before_instant,before_ref)=1)
      OR (before_kind='text' AND before_text IS NOT NULL AND num_nonnulls(before_bool,before_int,before_decimal,before_text,before_instant,before_ref)=1)
      OR (before_kind='instant' AND before_instant IS NOT NULL AND num_nonnulls(before_bool,before_int,before_decimal,before_text,before_instant,before_ref)=1)
      OR (before_kind IN ('entity','participant') AND before_ref IS NOT NULL AND num_nonnulls(before_bool,before_int,before_decimal,before_text,before_instant,before_ref)=1)
    );
  END IF;
END $bgwq_check$;
DO $bgwq_check$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'mutation_typed_after' AND conrelid = 'bgwq.event_mutations'::regclass) THEN
    ALTER TABLE bgwq.event_mutations ADD CONSTRAINT mutation_typed_after CHECK (
      (after_kind IS NULL AND num_nonnulls(after_bool,after_int,after_decimal,after_text,after_instant,after_ref)=0)
      OR (after_kind='none' AND num_nonnulls(after_bool,after_int,after_decimal,after_text,after_instant,after_ref)=0)
      OR (after_kind='bool' AND after_bool IS NOT NULL AND num_nonnulls(after_bool,after_int,after_decimal,after_text,after_instant,after_ref)=1)
      OR (after_kind='int' AND after_int IS NOT NULL AND num_nonnulls(after_bool,after_int,after_decimal,after_text,after_instant,after_ref)=1)
      OR (after_kind='decimal' AND after_decimal IS NOT NULL AND num_nonnulls(after_bool,after_int,after_decimal,after_text,after_instant,after_ref)=1)
      OR (after_kind='text' AND after_text IS NOT NULL AND num_nonnulls(after_bool,after_int,after_decimal,after_text,after_instant,after_ref)=1)
      OR (after_kind='instant' AND after_instant IS NOT NULL AND num_nonnulls(after_bool,after_int,after_decimal,after_text,after_instant,after_ref)=1)
      OR (after_kind IN ('entity','participant') AND after_ref IS NOT NULL AND num_nonnulls(after_bool,after_int,after_decimal,after_text,after_instant,after_ref)=1)
    );
  END IF;
END $bgwq_check$;

-- Supabase-managed auth.users is NOT created, altered, or migrated by Prisma.
-- Its external identity foreign keys are declared only as constraints against
-- UUID columns in bgwq-owned tables. Their referential behavior is RESTRICT.
DO $bgwq_auth$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_profiles_user_id_auth_users' AND conrelid = 'bgwq.profiles'::regclass) THEN
    ALTER TABLE bgwq."profiles" ADD CONSTRAINT "fk_profiles_user_id_auth_users" FOREIGN KEY ("user_id") REFERENCES auth.users(id) ON DELETE RESTRICT;
  END IF;
END $bgwq_auth$;
DO $bgwq_auth$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_definitions_owner_id_auth_users' AND conrelid = 'bgwq.definitions'::regclass) THEN
    ALTER TABLE bgwq."definitions" ADD CONSTRAINT "fk_definitions_owner_id_auth_users" FOREIGN KEY ("owner_id") REFERENCES auth.users(id) ON DELETE RESTRICT;
  END IF;
END $bgwq_auth$;
DO $bgwq_auth$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_games_creator_id_auth_users' AND conrelid = 'bgwq.games'::regclass) THEN
    ALTER TABLE bgwq."games" ADD CONSTRAINT "fk_games_creator_id_auth_users" FOREIGN KEY ("creator_id") REFERENCES auth.users(id) ON DELETE RESTRICT;
  END IF;
END $bgwq_auth$;
DO $bgwq_auth$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_participants_user_id_auth_users' AND conrelid = 'bgwq.participants'::regclass) THEN
    ALTER TABLE bgwq."participants" ADD CONSTRAINT "fk_participants_user_id_auth_users" FOREIGN KEY ("user_id") REFERENCES auth.users(id) ON DELETE RESTRICT;
  END IF;
END $bgwq_auth$;
DO $bgwq_auth$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_ratings_user_id_auth_users' AND conrelid = 'bgwq.ratings'::regclass) THEN
    ALTER TABLE bgwq."ratings" ADD CONSTRAINT "fk_ratings_user_id_auth_users" FOREIGN KEY ("user_id") REFERENCES auth.users(id) ON DELETE RESTRICT;
  END IF;
END $bgwq_auth$;

-- Database security and runtime integrity from the original database contract.
-- PostgreSQL-only invariants not representable by Prisma Schema Language.
-- Apply AFTER the Prisma-generated schema migration; review before production deployment.
-- This file is part of the declarative contract, not gameplay scripting.

REVOKE ALL ON SCHEMA bgwq FROM PUBLIC, anon, authenticated;
REVOKE ALL ON ALL TABLES IN SCHEMA bgwq FROM PUBLIC, anon, authenticated;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA bgwq FROM PUBLIC, anon, authenticated;

-- A version is frozen after publication, and publishing a version never
-- changes definitions pinned by existing games.
CREATE OR REPLACE FUNCTION bgwq.reject_published_version_mutation()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE v_id uuid;
BEGIN
  v_id := CASE WHEN TG_OP = 'INSERT' THEN NEW.version_id ELSE OLD.version_id END;
  -- Check the old owner on UPDATE as well as the new owner. Otherwise a
  -- published row could be moved into a draft and modified.
  IF EXISTS (SELECT 1 FROM bgwq.versions WHERE id = v_id AND published_at IS NOT NULL) THEN
    RAISE EXCEPTION 'published configuration is immutable: %', v_id USING ERRCODE = '23514';
  END IF;
  IF TG_OP = 'UPDATE' AND NEW.version_id IS DISTINCT FROM OLD.version_id
     AND EXISTS (SELECT 1 FROM bgwq.versions WHERE id = NEW.version_id AND published_at IS NOT NULL) THEN
    RAISE EXCEPTION 'published configuration is immutable: %', v_id USING ERRCODE = '23514';
  END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END;
$$;

-- This dynamic loop is DDL setup, NOT a gameplay execution interpreter.
DO $$
DECLARE table_name text;
BEGIN
  FOREACH table_name IN ARRAY ARRAY[
    'roles','phases','entity_types','entity_seeds','seed_links','fields',
    'seed_values','expressions','expression_arguments','actions',
    'action_parameters','phase_actions','effects','effect_arguments',
    'assets','visual_templates','visual_primitives'
  ] LOOP
    EXECUTE format('DROP TRIGGER IF EXISTS immutable_published ON bgwq.%I', table_name);
    EXECUTE format(
      'CREATE TRIGGER immutable_published BEFORE INSERT OR UPDATE OR DELETE ON bgwq.%I '
      || 'FOR EACH ROW EXECUTE FUNCTION bgwq.reject_published_version_mutation()',
      table_name
    );
  END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION bgwq.protect_version_header()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
  IF TG_OP = 'DELETE' AND OLD.published_at IS NOT NULL THEN
    RAISE EXCEPTION 'cannot delete published definition';
  END IF;
  IF TG_OP = 'UPDATE' AND OLD.published_at IS NOT NULL THEN
    RAISE EXCEPTION 'cannot mutate published definition';
  END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS immutable_version_header ON bgwq.versions;
CREATE TRIGGER immutable_version_header
BEFORE UPDATE OR DELETE ON bgwq.versions
FOR EACH ROW EXECUTE FUNCTION bgwq.protect_version_header();

-- Accepted history is append-only, including mutation arguments.
CREATE OR REPLACE FUNCTION bgwq.reject_history_mutation()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
  RAISE EXCEPTION 'accepted event log is append-only' USING ERRCODE = '23514';
END;
$$;
DROP TRIGGER IF EXISTS immutable_event ON bgwq.events;
CREATE TRIGGER immutable_event BEFORE UPDATE OR DELETE ON bgwq.events
FOR EACH ROW EXECUTE FUNCTION bgwq.reject_history_mutation();
DROP TRIGGER IF EXISTS immutable_event_values ON bgwq.event_values;
CREATE TRIGGER immutable_event_values BEFORE UPDATE OR DELETE ON bgwq.event_values
FOR EACH ROW EXECUTE FUNCTION bgwq.reject_history_mutation();
DROP TRIGGER IF EXISTS immutable_event_mutations ON bgwq.event_mutations;
CREATE TRIGGER immutable_event_mutations BEFORE UPDATE OR DELETE ON bgwq.event_mutations
FOR EACH ROW EXECUTE FUNCTION bgwq.reject_history_mutation();

-- Database-triggered revision hints never disclose hidden game state.
-- realtime.send takes JSONB because Supabase's transport requires JSON;
-- the payload is NOT an authoritative configuration/state JSONB column.
CREATE OR REPLACE FUNCTION bgwq.broadcast_revision()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
  PERFORM realtime.send(
    jsonb_build_object('game_id', NEW.game_id, 'revision', NEW.revision),
    'revision',
    'game:' || NEW.game_id::text,
    true
  );
  RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS emit_revision_hint ON bgwq.events;
CREATE TRIGGER emit_revision_hint AFTER INSERT ON bgwq.events
FOR EACH ROW EXECUTE FUNCTION bgwq.broadcast_revision();

-- Private realtime messages must only be readable by actual game members.
-- The database API remains private; this security-definer function reads
-- membership without granting table SELECT to frontend roles.
CREATE OR REPLACE FUNCTION bgwq.can_listen_to_game(topic text)
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path = '' AS $$
 SELECT topic LIKE 'game:%' AND (SELECT auth.uid()) IS NOT NULL AND EXISTS (
   SELECT 1 FROM bgwq.participants p
   WHERE p.game_id::text = split_part(topic, ':', 2)
     AND p.user_id = (SELECT auth.uid())
 );
$$;
REVOKE ALL ON FUNCTION bgwq.can_listen_to_game(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION bgwq.can_listen_to_game(text) TO authenticated;

DROP POLICY IF EXISTS bgwq_game_broadcast_read ON realtime.messages;
CREATE POLICY bgwq_game_broadcast_read ON realtime.messages
FOR SELECT TO authenticated
USING (bgwq.can_listen_to_game(realtime.topic()));

-- Private schema usage permits the explicitly granted policy helper to be called;
-- no application table privileges are granted to browser roles.
GRANT USAGE ON SCHEMA bgwq TO authenticated;

-- A game must pin a published definition at creation. Publication is the only
-- point at which the complete type graph is accepted by the API validator.
CREATE OR REPLACE FUNCTION bgwq.assert_game_definition_published()
RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path = '' AS $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM bgwq.versions v
    WHERE v.id = NEW.version_id AND v.published_at IS NOT NULL
  ) THEN
    RAISE EXCEPTION 'a game must pin a published definition version'
      USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS game_requires_publication ON bgwq.games;
CREATE TRIGGER game_requires_publication
BEFORE INSERT OR UPDATE OF version_id ON bgwq.games
FOR EACH ROW EXECUTE FUNCTION bgwq.assert_game_definition_published();

-- Outcome rows are immutable settlement records; account ratings/awards may be
-- updated by authorized settlement services but never by author-defined effects.
DROP TRIGGER IF EXISTS immutable_game_outcomes ON bgwq.game_outcomes;
CREATE TRIGGER immutable_game_outcomes BEFORE UPDATE OR DELETE ON bgwq.game_outcomes
FOR EACH ROW EXECUTE FUNCTION bgwq.reject_history_mutation();

-- Check event/revision parity at COMMIT, after the service has written both the
-- materialized state and its immutable event. This detects missing or orphan
-- accepted events without requiring the HTTP layer to write event logs first.
CREATE OR REPLACE FUNCTION bgwq.assert_game_event_parity()
RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path = '' AS $$
DECLARE
  the_game uuid;
  g bgwq.games%ROWTYPE;
  n bigint;
  top_revision bigint;
BEGIN
  the_game := CASE WHEN TG_TABLE_NAME = 'games' THEN NEW.id ELSE NEW.game_id END;
  SELECT * INTO g FROM bgwq.games WHERE id = the_game;
  IF NOT FOUND THEN RETURN NULL; END IF;
  SELECT count(*), max(revision) INTO n, top_revision
    FROM bgwq.events WHERE game_id = the_game;
  IF g.status = 'finished' AND
     (SELECT count(*) FROM bgwq.game_outcomes WHERE game_id = the_game)
         <> (SELECT count(*) FROM bgwq.participants WHERE game_id = the_game) THEN
    RAISE EXCEPTION 'finished game requires a final result for each participant' USING ERRCODE='23514';
  END IF;
  IF g.status IN ('pending','expired') THEN
    IF n <> 0 THEN
      RAISE EXCEPTION 'pre-activation game has accepted events' USING ERRCODE='23514';
    END IF;
  ELSIF n <> g.revision + 1 OR top_revision <> g.revision THEN
    RAISE EXCEPTION 'game revision % differs from immutable event history for %',g.revision,the_game
      USING ERRCODE='23514';
  END IF;
  RETURN NULL;
END;
$$;
DROP TRIGGER IF EXISTS check_game_revision_history ON bgwq.games;
CREATE CONSTRAINT TRIGGER check_game_revision_history
AFTER INSERT OR UPDATE ON bgwq.games
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION bgwq.assert_game_event_parity();
DROP TRIGGER IF EXISTS check_event_revision_history ON bgwq.events;
CREATE CONSTRAINT TRIGGER check_event_revision_history
AFTER INSERT ON bgwq.events
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION bgwq.assert_game_event_parity();
