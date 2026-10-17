# BoardGamesWithQuests — SCHEMA


## 1. Drizzle — normative PostgreSQL table schema

This TypeScript module is the complete authored schema for table definitions, enum types, indexes and foreign keys. Documentation is inline as TSDoc. Supabase Auth's `auth.users` is an external existing table. All authoritative game state is relational; permitted JSON on the HTTP wire and private Broadcast transport is not game storage.

```typescript
/**
 * BoardGamesWithQuests authoritative declarative PostgreSQL schema.
 *
 * Database shape is authored here; Drizzle never participates in runtime gameplay.
 * Python/FastAPI accesses the provisioned database through psycopg.
 * All client-visible data must pass through projection-level authorization.
 *
 * Invariants requiring transactions/triggers (immutable publications, revision/event
 * parity, private Broadcast, actor ownership) are implemented in guarded SQL
 * generated/applied with the corresponding reviewed Supabase migrations.
 * @packageDocumentation
 */
import { sql } from 'drizzle-orm';
import { authUsers } from 'drizzle-orm/supabase';
import {
  pgSchema, uuid, text, integer, bigint, numeric, boolean, timestamp,
  uniqueIndex, index, primaryKey, foreignKey, check,
} from 'drizzle-orm/pg-core';

const bgwq = pgSchema('bgwq');

export const entityKind = bgwq.enum('entity_kind', ['game','space','item','objective']);
export const gameStatus = bgwq.enum('game_status', ['pending','active','finished','expired']);
export const valueKind = bgwq.enum('value_kind', ['bool','int','decimal','text','instant','entity','participant','none']);
export const triggerKind = bgwq.enum('trigger_kind', ['command','hook']);
export const operationKind = bgwq.enum('operation_kind', ['insert','set','remove']);
export const assetStatus = bgwq.enum('asset_status', ['staged','ready']);

const id = () => uuid('id').primaryKey().defaultRandom();
const version = () => uuid('version_id').notNull();
const game = () => uuid('game_id').notNull();
const created = () => timestamp('created_at', { withTimezone: true }).notNull().defaultNow();

/** Display profile; auth.users is authoritative for identity. */
export const profiles = bgwq.table('profiles', {
  userId: uuid('user_id').primaryKey().references(() => authUsers.id, { onDelete:'restrict' }),
  displayName: text('display_name').notNull(), username: text('username').unique(), createdAt: created(),
});
/** Published and user-owned game families. */
export const definitions = bgwq.table('definitions', {
  id: id(), ownerId: uuid('owner_id').references(() => authUsers.id, { onDelete:'restrict' }),
  key: text('key').notNull(), name: text('name').notNull(), description: text('description'),
  builtIn: boolean('built_in').notNull().default(false), createdAt: created(),
}, t => [uniqueIndex('definition_owner_key').on(t.ownerId, t.key).where(sql`${t.ownerId} IS NOT NULL`),
  uniqueIndex('builtin_definition_key').on(t.key).where(sql`${t.builtIn}`),
  check('definition_builtin_ownership', sql`${t.builtIn} = (${t.ownerId} IS NULL)`)]);
/** Immutable after publication; version is pinned for the lifetime of a game. */
export const versions = bgwq.table('versions', {
  id: id(), definitionId: uuid('definition_id').notNull().references(() => definitions.id, { onDelete:'restrict' }),
  number: integer('number').notNull(), minimumParticipants: integer('minimum_participants').notNull(),
  maximumParticipants: integer('maximum_participants').notNull(),
  semanticsVersion: integer('semantics_version').notNull().default(1),
  publishedAt: timestamp('published_at', { withTimezone:true }), createdAt: created(),
}, t => [uniqueIndex('version_number_unique').on(t.definitionId,t.number),
  check('version_bounds',sql`${t.minimumParticipants}>0 AND ${t.maximumParticipants}>=${t.minimumParticipants}`)]);
/** Player roles, independent of fixed chess sides. */
export const roles = bgwq.table('roles', {
  id:id(), versionId:version(), key:text('key').notNull(), label:text('label').notNull(),
  forwardRow:integer('forward_row'), minimumCount:integer('minimum_count').notNull().default(0), maximumCount:integer('maximum_count').notNull().default(1),
},t=>[foreignKey({columns:[t.versionId],foreignColumns:[versions.id]}),
  uniqueIndex('role_version_key').on(t.versionId,t.key),uniqueIndex('role_version_id').on(t.versionId,t.id),
  check('role_count',sql`${t.minimumCount}>=0 AND ${t.maximumCount}>=${t.minimumCount}`),
  check('role_forward_row',sql`${t.forwardRow} IS NULL OR ${t.forwardRow} IN (-1,1)`)]);
/** Turn/decision phase; transitions are configured actions. */
export const phases = bgwq.table('phases', {
  id:id(),versionId:version(),key:text('key').notNull(),label:text('label').notNull(),
  initial:boolean('initial').notNull().default(false),ordinal:integer('ordinal').notNull().default(0),
},t=>[foreignKey({columns:[t.versionId],foreignColumns:[versions.id]}),
  uniqueIndex('phase_version_key').on(t.versionId,t.key), uniqueIndex('phase_version_id').on(t.versionId,t.id),
  uniqueIndex('phase_single_initial').on(t.versionId).where(sql`${t.initial}`)]);
/** Types of entities: one of game, space, item, objective. */
export const entityTypes = bgwq.table('entity_types', {
  id:id(),versionId:version(),key:text('key').notNull(),name:text('name').notNull(),
  kind:entityKind('kind').notNull(),
},t=>[foreignKey({columns:[t.versionId],foreignColumns:[versions.id]}),
  uniqueIndex('entity_type_key').on(t.versionId,t.key),uniqueIndex('entity_type_version_id').on(t.versionId,t.id)]);
/** Topology and game placement are entity-to-entity relationships, not a fixed grid. */
export const entitySeeds = bgwq.table('entity_seeds', {
  id:id(),versionId:version(),key:text('key').notNull(),entityTypeId:uuid('entity_type_id').notNull(),
  ownerSeat:integer('owner_seat'),parentId:uuid('parent_id'),locationId:uuid('location_id'),
  ordinal:integer('ordinal'),row:integer('row'),column:integer('column'),
  x:numeric('x'),y:numeric('y'),
},t=>[foreignKey({columns:[t.versionId,t.entityTypeId],foreignColumns:[entityTypes.versionId,entityTypes.id]}),
  foreignKey({columns:[t.versionId,t.parentId],foreignColumns:[t.versionId,t.id]}),
  foreignKey({columns:[t.versionId,t.locationId],foreignColumns:[t.versionId,t.id]}),
  uniqueIndex('seed_version_key').on(t.versionId,t.key), uniqueIndex('seed_version_id').on(t.versionId,t.id),
  check('seed_not_self',sql`${t.parentId} IS DISTINCT FROM ${t.id} AND ${t.locationId} IS DISTINCT FROM ${t.id}`)]);
/** Definition links encode adjacency, directed tracks, membership, and groupings. */
export const seedLinks = bgwq.table('seed_links', {
  id:id(),versionId:version(),sourceId:uuid('source_id').notNull(),targetId:uuid('target_id').notNull(),
  relation:text('relation').notNull(),ordinal:integer('ordinal').notNull().default(0),
},t=>[foreignKey({columns:[t.versionId,t.sourceId],foreignColumns:[entitySeeds.versionId,entitySeeds.id]}),
  foreignKey({columns:[t.versionId,t.targetId],foreignColumns:[entitySeeds.versionId,entitySeeds.id]}),
  uniqueIndex('seed_link_unique').on(t.versionId,t.sourceId,t.targetId,t.relation)]);
/** State fields typed per entity definition, also used for objectives. */
export const fields = bgwq.table('fields', {
  id:id(),versionId:version(),entityTypeId:uuid('entity_type_id').notNull(),key:text('key').notNull(),
  typeKey:text('type_key').notNull(),nullable:boolean('nullable').notNull().default(false),
},t=>[foreignKey({columns:[t.versionId,t.entityTypeId],foreignColumns:[entityTypes.versionId,entityTypes.id]}),
  uniqueIndex('field_entity_key').on(t.entityTypeId,t.key),uniqueIndex('field_version_id').on(t.versionId,t.id)]);
/** Typed defaults and initial values are stored in columns; no JSONB. */
export const seedValues = bgwq.table('seed_values', {
  seedId:uuid('seed_id').notNull(),versionId:version(),fieldId:uuid('field_id').notNull(),
  kind:valueKind('kind').notNull(),bool:boolean('bool_value'),int:bigint('int_value',{mode:'bigint'}),
  decimal:numeric('decimal_value'),text:text('text_value'),instant:timestamp('instant_value',{withTimezone:true}),
  refSeedId:uuid('ref_seed_id'),refSeat:integer('ref_seat'),
},t=>[primaryKey({columns:[t.seedId,t.fieldId]}),
  foreignKey({columns:[t.versionId,t.seedId],foreignColumns:[entitySeeds.versionId,entitySeeds.id]}),
  foreignKey({columns:[t.versionId,t.fieldId],foreignColumns:[fields.versionId,fields.id]}),
  foreignKey({columns:[t.versionId,t.refSeedId],foreignColumns:[entitySeeds.versionId,entitySeeds.id]}),
  check('seed_value_one_payload',sql`
    (${t.kind}='none' AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.refSeedId},${t.refSeat})=0) OR
    (${t.kind}='bool' AND ${t.bool} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.refSeedId},${t.refSeat})=1) OR
    (${t.kind}='int' AND ${t.int} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.refSeedId},${t.refSeat})=1) OR
    (${t.kind}='decimal' AND ${t.decimal} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.refSeedId},${t.refSeat})=1) OR
    (${t.kind}='text' AND ${t.text} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.refSeedId},${t.refSeat})=1) OR
    (${t.kind}='instant' AND ${t.instant} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.refSeedId},${t.refSeat})=1) OR
    (${t.kind}='entity' AND ${t.refSeedId} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.refSeedId},${t.refSeat})=1) OR
    (${t.kind}='participant' AND ${t.refSeat} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.refSeedId},${t.refSeat})=1)
  `)]);
/** Immutable registry metadata; executable operators are implemented only in engine. */
export const operators = bgwq.table('operators', {
  key:text('key').primaryKey(),kind:text('kind').notNull(),returns:text('returns'),
  summary:text('summary').notNull(),
},t=>[check('operator_kind',sql`${t.kind} IN ('expression','effect')`)]);
export const operatorParameters = bgwq.table('operator_parameters', {
  operatorKey:text('operator_key').notNull().references(()=>operators.key),
  key:text('key').notNull(),typeKey:text('type_key').notNull(),
  ordinal:integer('ordinal').notNull(),required:boolean('required').notNull().default(true),
  variadic:boolean('variadic').notNull().default(false),
},t=>[primaryKey({columns:[t.operatorKey,t.key]}),uniqueIndex('operator_param_order').on(t.operatorKey,t.ordinal)]);
export const hooks = bgwq.table('hooks', {
  key:text('key').primaryKey(),ordinal:integer('ordinal').notNull().unique(),summary:text('summary').notNull(),
});
/** Acyclic, reusable expression DAG; conditions are bool-valued expressions. */
export const expressions = bgwq.table('expressions', {
  id:id(),versionId:version(),key:text('key'),kind:text('kind').notNull(),resultType:text('result_type').notNull(),
  literalKind:valueKind('literal_kind'),literalBool:boolean('literal_bool'),literalInt:bigint('literal_int',{mode:'bigint'}),
  literalDecimal:numeric('literal_decimal'),literalText:text('literal_text'),
  literalInstant:timestamp('literal_instant',{withTimezone:true}),
  referenceKey:text('reference_key'),fieldId:uuid('field_id'),operatorKey:text('operator_key').references(()=>operators.key),
},t=>[foreignKey({columns:[t.versionId],foreignColumns:[versions.id]}),
  foreignKey({columns:[t.versionId,t.fieldId],foreignColumns:[fields.versionId,fields.id]}),
  uniqueIndex('expr_version_id').on(t.versionId,t.id),uniqueIndex('expr_version_key').on(t.versionId,t.key),
  check('expression_kind',sql`${t.kind} IN ('literal','context','field','local','call')`)]);
export const expressionArguments = bgwq.table('expression_arguments', {
  versionId:version(),parentId:uuid('parent_id').notNull(),childId:uuid('child_id').notNull(),
  parameter:text('parameter').notNull(),ordinal:integer('ordinal').notNull().default(0),
},t=>[primaryKey({columns:[t.parentId,t.parameter,t.ordinal]}),
  foreignKey({columns:[t.versionId,t.parentId],foreignColumns:[expressions.versionId,expressions.id]}),
  foreignKey({columns:[t.versionId,t.childId],foreignColumns:[expressions.versionId,expressions.id]}),
  check('expression_not_self',sql`${t.parentId}<>${t.childId}`)]);
/** Manual commands and automatic hook actions share one implementation. */
export const actions = bgwq.table('actions', {
  id:id(),versionId:version(),entityTypeId:uuid('entity_type_id').notNull(),key:text('key').notNull(),
  title:text('title').notNull(),trigger:triggerKind('trigger').notNull(),hookKey:text('hook_key').references(()=>hooks.key),
  iteratorExpressionId:uuid('iterator_expression_id'),iteratorVar:text('iterator_var'),
  conditionExpressionId:uuid('condition_expression_id'),priority:integer('priority').notNull().default(0),
  enabled:boolean('enabled').notNull().default(true),
},t=>[foreignKey({columns:[t.versionId,t.entityTypeId],foreignColumns:[entityTypes.versionId,entityTypes.id]}),
  foreignKey({columns:[t.versionId,t.iteratorExpressionId],foreignColumns:[expressions.versionId,expressions.id]}),
  foreignKey({columns:[t.versionId,t.conditionExpressionId],foreignColumns:[expressions.versionId,expressions.id]}),
  uniqueIndex('action_owner_key').on(t.entityTypeId,t.key),uniqueIndex('action_version_id').on(t.versionId,t.id),
  index('action_hook_order').on(t.trigger,t.hookKey,t.priority),
  check('action_trigger_check',sql`(${t.trigger}='command' AND ${t.hookKey} IS NULL) OR (${t.trigger}='hook' AND ${t.hookKey} IS NOT NULL)`),
  check('action_iterator_pair',sql`(${t.iteratorExpressionId} IS NULL) = (${t.iteratorVar} IS NULL)`)]);
export const actionParameters = bgwq.table('action_parameters', {
  versionId:version(),actionId:uuid('action_id').notNull(),key:text('key').notNull(),typeKey:text('type_key').notNull(),
  required:boolean('required').notNull().default(true),ordinal:integer('ordinal').notNull().default(0),
},t=>[primaryKey({columns:[t.actionId,t.key]}),
  foreignKey({columns:[t.versionId,t.actionId],foreignColumns:[actions.versionId,actions.id]})]);
export const phaseActions = bgwq.table('phase_actions', {
  versionId:version(),phaseId:uuid('phase_id').notNull(),actionId:uuid('action_id').notNull(),
},t=>[primaryKey({columns:[t.phaseId,t.actionId]}),
  foreignKey({columns:[t.versionId,t.phaseId],foreignColumns:[phases.versionId,phases.id]}),
  foreignKey({columns:[t.versionId,t.actionId],foreignColumns:[actions.versionId,actions.id]})]);
/** Effects of any action are ordered, typed, and executed only on proposed state. */
export const effects = bgwq.table('effects', {
  id:id(),versionId:version(),actionId:uuid('action_id').notNull(),ordinal:integer('ordinal').notNull(),
  operatorKey:text('operator_key').notNull().references(()=>operators.key),
  conditionExpressionId:uuid('condition_expression_id'),
},t=>[foreignKey({columns:[t.versionId,t.actionId],foreignColumns:[actions.versionId,actions.id]}),
  foreignKey({columns:[t.versionId,t.conditionExpressionId],foreignColumns:[expressions.versionId,expressions.id]}),
  uniqueIndex('effect_version_id').on(t.versionId,t.id),uniqueIndex('effect_action_order').on(t.actionId,t.ordinal)]);
export const effectArguments = bgwq.table('effect_arguments', {
  versionId:version(),effectId:uuid('effect_id').notNull(),expressionId:uuid('expression_id').notNull(),
  key:text('key').notNull(),ordinal:integer('ordinal').notNull().default(0),
},t=>[primaryKey({columns:[t.effectId,t.key,t.ordinal]}),
  foreignKey({columns:[t.versionId,t.effectId],foreignColumns:[effects.versionId,effects.id]}),
  foreignKey({columns:[t.versionId,t.expressionId],foreignColumns:[expressions.versionId,expressions.id]})]);

/** Binary assets live in Supabase Storage, never in configuration rows. */
export const assets = bgwq.table('assets', {
  id:id(),versionId:version(),key:text('key').notNull(),bucket:text('bucket').notNull(),
  path:text('path').notNull(),mime:text('mime').notNull(),bytes:bigint('bytes',{mode:'bigint'}).notNull(),
  sha256:text('sha256').notNull(),status:assetStatus('status').notNull().default('staged'),
},t=>[foreignKey({columns:[t.versionId],foreignColumns:[versions.id]}),
  uniqueIndex('asset_version_key').on(t.versionId,t.key),uniqueIndex('asset_version_id').on(t.versionId,t.id),
  uniqueIndex('asset_storage_path').on(t.bucket,t.path),
  check('asset_size',sql`${t.bytes} BETWEEN 1 AND 2097152`),
  check('asset_hash_lower_hex',sql`${t.sha256} ~ '^[0-9a-f]{64}$'`),
  check('asset_supported_mime',sql`${t.mime} IN ('image/png','image/webp')`),
  check('asset_path_nonempty',sql`length(btrim(${t.path}))>0`)]);
/** Generic SVG presentation associated with any configured entity type. */
export const visualTemplates = bgwq.table('visual_templates', {
  id:id(),versionId:version(),entityTypeId:uuid('entity_type_id').notNull(),key:text('key').notNull(),
},t=>[foreignKey({columns:[t.versionId,t.entityTypeId],foreignColumns:[entityTypes.versionId,entityTypes.id]}),
  uniqueIndex('visual_type_key').on(t.entityTypeId,t.key),uniqueIndex('visual_template_version_id').on(t.versionId,t.id)]);
export const visualPrimitives = bgwq.table('visual_primitives', {
  id:id(),versionId:version(),templateId:uuid('template_id').notNull(),kind:text('kind').notNull(),
  layer:integer('layer').notNull().default(0),ordinal:integer('ordinal').notNull().default(0),
  x:numeric('x').notNull().default('0'),y:numeric('y').notNull().default('0'),
  width:numeric('width'),height:numeric('height'),d:text('path_data'),text:text('text_content'),
  fill:text('fill'),stroke:text('stroke'),assetId:uuid('asset_id'),
},t=>[foreignKey({columns:[t.versionId,t.templateId],foreignColumns:[visualTemplates.versionId,visualTemplates.id]}),
  foreignKey({columns:[t.versionId,t.assetId],foreignColumns:[assets.versionId,assets.id]}),
  uniqueIndex('visual_primitive_order').on(t.templateId,t.layer,t.ordinal),
  check('visual_primitive_kind',sql`${t.kind} IN ('rectangle','ellipse','line','path','text','image')`)]);

/** A game locks to one published definition version. */
export const games = bgwq.table('games', {
  id:id(),versionId:version(),creatorId:uuid('creator_id').notNull().references(()=>authUsers.id),
  creationKey:text('creation_key').notNull(),status:gameStatus('status').notNull().default('pending'),
  revision:bigint('revision',{mode:'bigint'}).notNull().default(0),
  phaseId:uuid('phase_id'),turn:bigint('turn',{mode:'bigint'}).notNull().default(0),
  createdAt:created(),startedAt:timestamp('started_at',{withTimezone:true}),
  finishedAt:timestamp('finished_at',{withTimezone:true}),
  expiresAt:timestamp('expires_at',{withTimezone:true}).notNull(),
},t=>[foreignKey({columns:[t.versionId],foreignColumns:[versions.id]}),
  foreignKey({columns:[t.versionId,t.phaseId],foreignColumns:[phases.versionId,phases.id]}),
  uniqueIndex('game_version_id').on(t.id,t.versionId),uniqueIndex('game_creation_key').on(t.creatorId,t.creationKey),
  index('games_expiry').on(t.status,t.expiresAt),check('game_revision_nonnegative',sql`${t.revision}>=0 AND ${t.turn}>=0`),
  check('game_lifecycle_timestamps',sql`
    (${t.status}='pending' AND ${t.startedAt} IS NULL AND ${t.finishedAt} IS NULL)
    OR (${t.status}='expired' AND ${t.startedAt} IS NULL AND ${t.finishedAt} IS NULL)
    OR (${t.status}='active' AND ${t.startedAt} IS NOT NULL AND ${t.finishedAt} IS NULL)
    OR (${t.status}='finished' AND ${t.startedAt} IS NOT NULL AND ${t.finishedAt} IS NOT NULL)
  `)]);
export const participants = bgwq.table('participants', {
  id:id(),gameId:game(),versionId:version(),userId:uuid('user_id').notNull().references(()=>authUsers.id),
  roleId:uuid('role_id').notNull(),seat:integer('seat').notNull(),
  eliminatedAt:timestamp('eliminated_at',{withTimezone:true}),joinedAt:created(),
},t=>[foreignKey({columns:[t.gameId,t.versionId],foreignColumns:[games.id,games.versionId]}),
  foreignKey({columns:[t.versionId,t.roleId],foreignColumns:[roles.versionId,roles.id]}),
  uniqueIndex('participant_game_id').on(t.gameId,t.id),uniqueIndex('participant_user_game').on(t.gameId,t.userId),
  uniqueIndex('participant_seat').on(t.gameId,t.seat),index('participant_by_user').on(t.userId,t.gameId),
  check('participant_seat_nonnegative',sql`${t.seat}>=0`)]);
export const activeParticipants = bgwq.table('active_participants', {
  gameId:game(),participantId:uuid('participant_id').notNull(),
},t=>[primaryKey({columns:[t.gameId,t.participantId]}),
  foreignKey({columns:[t.gameId,t.participantId],foreignColumns:[participants.gameId,participants.id]})]);
/** Dynamic runtime instances; spaces, pieces, cards and objectives are entities. */
export const gameEntities = bgwq.table('game_entities', {
  id:id(),gameId:game(),versionId:version(),entityTypeId:uuid('entity_type_id').notNull(),
  seedId:uuid('seed_id'),ownerId:uuid('owner_id'),parentId:uuid('parent_id'),locationId:uuid('location_id'),
  ordinal:integer('ordinal'),createdRevision:bigint('created_revision',{mode:'bigint'}).notNull(),
  removedRevision:bigint('removed_revision',{mode:'bigint'}),
},t=>[foreignKey({columns:[t.gameId,t.versionId],foreignColumns:[games.id,games.versionId]}),
  foreignKey({columns:[t.versionId,t.entityTypeId],foreignColumns:[entityTypes.versionId,entityTypes.id]}),
  foreignKey({columns:[t.versionId,t.seedId],foreignColumns:[entitySeeds.versionId,entitySeeds.id]}),
  foreignKey({columns:[t.gameId,t.ownerId],foreignColumns:[participants.gameId,participants.id]}),
  foreignKey({columns:[t.gameId,t.parentId],foreignColumns:[t.gameId,t.id]}),
  foreignKey({columns:[t.gameId,t.locationId],foreignColumns:[t.gameId,t.id]}),
  uniqueIndex('game_entity_game_id').on(t.gameId,t.id),
  uniqueIndex('game_entity_seed_unique').on(t.gameId,t.seedId).where(sql`${t.seedId} IS NOT NULL`),
  index('game_entity_location').on(t.gameId,t.locationId),
  check('runtime_entity_self',sql`${t.id} IS DISTINCT FROM ${t.parentId} AND ${t.id} IS DISTINCT FROM ${t.locationId}`)]);
export const gameLinks = bgwq.table('game_links', {
  id:id(),gameId:game(),sourceId:uuid('source_id').notNull(),targetId:uuid('target_id').notNull(),
  relation:text('relation').notNull(),ordinal:integer('ordinal').notNull().default(0),
},t=>[foreignKey({columns:[t.gameId,t.sourceId],foreignColumns:[gameEntities.gameId,gameEntities.id]}),
  foreignKey({columns:[t.gameId,t.targetId],foreignColumns:[gameEntities.gameId,gameEntities.id]}),
  uniqueIndex('game_link_pair').on(t.gameId,t.sourceId,t.targetId,t.relation)]);
/** One typed value per entity field; reference payloads use scoped FKs. */
export const gameValues = bgwq.table('game_values', {
  gameId:game(),versionId:version(),entityId:uuid('entity_id').notNull(),fieldId:uuid('field_id').notNull(),
  kind:valueKind('kind').notNull(),bool:boolean('bool_value'),int:bigint('int_value',{mode:'bigint'}),
  decimal:numeric('decimal_value'),text:text('text_value'),instant:timestamp('instant_value',{withTimezone:true}),
  refEntityId:uuid('ref_entity_id'),refParticipantId:uuid('ref_participant_id'),
  updatedRevision:bigint('updated_revision',{mode:'bigint'}).notNull(),
},t=>[primaryKey({columns:[t.entityId,t.fieldId]}),
  foreignKey({columns:[t.gameId,t.versionId],foreignColumns:[games.id,games.versionId]}),
  foreignKey({columns:[t.gameId,t.entityId],foreignColumns:[gameEntities.gameId,gameEntities.id]}),
  foreignKey({columns:[t.versionId,t.fieldId],foreignColumns:[fields.versionId,fields.id]}),
  foreignKey({columns:[t.gameId,t.refEntityId],foreignColumns:[gameEntities.gameId,gameEntities.id]}),
  foreignKey({columns:[t.gameId,t.refParticipantId],foreignColumns:[participants.gameId,participants.id]}),
  check('game_value_exactly_one',sql`
    (${t.kind}='none' AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.refEntityId},${t.refParticipantId})=0)
    OR (${t.kind}='bool' AND ${t.bool} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.refEntityId},${t.refParticipantId})=1)
    OR (${t.kind}='int' AND ${t.int} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.refEntityId},${t.refParticipantId})=1)
    OR (${t.kind}='decimal' AND ${t.decimal} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.refEntityId},${t.refParticipantId})=1)
    OR (${t.kind}='text' AND ${t.text} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.refEntityId},${t.refParticipantId})=1)
    OR (${t.kind}='instant' AND ${t.instant} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.refEntityId},${t.refParticipantId})=1)
    OR (${t.kind}='entity' AND ${t.refEntityId} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.refEntityId},${t.refParticipantId})=1)
    OR (${t.kind}='participant' AND ${t.refParticipantId} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.refEntityId},${t.refParticipantId})=1)
  `)]);
/**
 * Runtime typed collections/records for trade proposals, bids, and action parameters.
 * No JSONB document stores authoritative composite state. A composite is an
 * ordered list or keyed record. Nested composites use a scoped child reference;
 * the transaction validator rejects cycles, dangling references, and type drift.
 */
export const gameComposites = bgwq.table('game_composites', {
  id: id(), gameId: game(), versionId: version(),
  ownerEntityId: uuid('owner_entity_id').notNull(), fieldId: uuid('field_id').notNull(),
  containerKind: text('container_kind').notNull(), typeKey: text('type_key').notNull(),
  createdRevision: bigint('created_revision', { mode:'bigint' }).notNull(),
}, t => [
  foreignKey({columns:[t.gameId,t.versionId],foreignColumns:[games.id,games.versionId]}),
  foreignKey({columns:[t.gameId,t.ownerEntityId],foreignColumns:[gameEntities.gameId,gameEntities.id]}),
  foreignKey({columns:[t.versionId,t.fieldId],foreignColumns:[fields.versionId,fields.id]}),
  uniqueIndex('game_composite_game_id').on(t.gameId,t.id),
  uniqueIndex('game_composite_owner_field').on(t.ownerEntityId,t.fieldId),
  check('game_composite_kind',sql`${t.containerKind} IN ('list','record')`),
]);
/** A typed member of one normalized runtime list/record. */
export const gameCompositeEntries = bgwq.table('game_composite_entries', {
  id:id(), gameId:game(), compositeId:uuid('composite_id').notNull(),
  ordinal:integer('ordinal').notNull(), memberKey:text('member_key'),
  kind:valueKind('kind'), bool:boolean('bool_value'),
  int:bigint('int_value',{mode:'bigint'}), decimal:numeric('decimal_value'),
  text:text('text_value'), instant:timestamp('instant_value',{withTimezone:true}),
  refEntityId:uuid('ref_entity_id'),refParticipantId:uuid('ref_participant_id'),
  childCompositeId:uuid('child_composite_id'),
}, t => [
  foreignKey({columns:[t.gameId,t.compositeId],foreignColumns:[gameComposites.gameId,gameComposites.id]}),
  foreignKey({columns:[t.gameId,t.childCompositeId],foreignColumns:[gameComposites.gameId,gameComposites.id]}),
  foreignKey({columns:[t.gameId,t.refEntityId],foreignColumns:[gameEntities.gameId,gameEntities.id]}),
  foreignKey({columns:[t.gameId,t.refParticipantId],foreignColumns:[participants.gameId,participants.id]}),
  uniqueIndex('game_composite_entry_order').on(t.compositeId,t.ordinal),
  uniqueIndex('game_composite_record_key').on(t.compositeId,t.memberKey).where(sql`${t.memberKey} IS NOT NULL`),
  check('game_composite_entry_index',sql`${t.ordinal}>=0`),
  check('game_composite_entry_value',sql`
    (${t.kind} IS NULL AND ${t.childCompositeId} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.refEntityId},${t.refParticipantId},${t.childCompositeId})=1)
    OR (${t.kind}='bool' AND ${t.bool} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.refEntityId},${t.refParticipantId},${t.childCompositeId})=1)
    OR (${t.kind}='int' AND ${t.int} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.refEntityId},${t.refParticipantId},${t.childCompositeId})=1)
    OR (${t.kind}='decimal' AND ${t.decimal} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.refEntityId},${t.refParticipantId},${t.childCompositeId})=1)
    OR (${t.kind}='text' AND ${t.text} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.refEntityId},${t.refParticipantId},${t.childCompositeId})=1)
    OR (${t.kind}='instant' AND ${t.instant} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.refEntityId},${t.refParticipantId},${t.childCompositeId})=1)
    OR (${t.kind}='entity' AND ${t.refEntityId} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.refEntityId},${t.refParticipantId},${t.childCompositeId})=1)
    OR (${t.kind}='participant' AND ${t.refParticipantId} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.refEntityId},${t.refParticipantId},${t.childCompositeId})=1)
  `),
  check('game_composite_no_self',sql`${t.compositeId} IS DISTINCT FROM ${t.childCompositeId}`),
]);

/** Time controls are optional; trusted time is provided by the server/DB. */
export const clocks = bgwq.table('clocks', {
  gameId:game(),participantId:uuid('participant_id').notNull(),
  remainingMs:bigint('remaining_ms',{mode:'bigint'}).notNull(),incrementMs:bigint('increment_ms',{mode:'bigint'}).notNull().default(0),
  anchorAt:timestamp('anchor_at',{withTimezone:true}),paused:boolean('paused').notNull().default(false),
},t=>[primaryKey({columns:[t.gameId,t.participantId]}),
  foreignKey({columns:[t.gameId,t.participantId],foreignColumns:[participants.gameId,participants.id]}),
  check('clock_nonnegative',sql`${t.remainingMs}>=0 AND ${t.incrementMs}>=0`)]);
/** One accepted command -> one immutable revision event. */
export const events = bgwq.table('events', {
  id:id(),gameId:game(),revision:bigint('revision',{mode:'bigint'}).notNull(),
  actorId:uuid('actor_id'),actionKey:text('action_key').notNull(),requestId:text('request_id'),
  requestDigest:text('request_digest'),semanticsVersion:integer('semantics_version').notNull(),
  occurredAt:timestamp('occurred_at',{withTimezone:true}).notNull(),
  beforeDigest:text('before_digest'),afterDigest:text('after_digest'),
},t=>[foreignKey({columns:[t.gameId],foreignColumns:[games.id]}),
  foreignKey({columns:[t.gameId,t.actorId],foreignColumns:[participants.gameId,participants.id]}),
  uniqueIndex('event_game_revision').on(t.gameId,t.revision),uniqueIndex('event_game_id').on(t.gameId,t.id),
  uniqueIndex('event_idempotency').on(t.gameId,t.requestId).where(sql`${t.requestId} IS NOT NULL`)]);
/** Event arguments encode scalars, refs and ordered lists through position; no JSONB. */
export const eventValues = bgwq.table('event_values', {
  id:id(),gameId:game(),eventId:uuid('event_id').notNull(),category:text('category').notNull(),
  key:text('key').notNull(),ordinal:integer('ordinal').notNull().default(0),
  kind:valueKind('kind').notNull(),bool:boolean('bool_value'),int:bigint('int_value',{mode:'bigint'}),
  decimal:numeric('decimal_value'),text:text('text_value'),instant:timestamp('instant_value',{withTimezone:true}),
  entityId:uuid('entity_id'),participantId:uuid('participant_id'),
},t=>[foreignKey({columns:[t.gameId,t.eventId],foreignColumns:[events.gameId,events.id]}),
  foreignKey({columns:[t.gameId,t.entityId],foreignColumns:[gameEntities.gameId,gameEntities.id]}),
  foreignKey({columns:[t.gameId,t.participantId],foreignColumns:[participants.gameId,participants.id]}),
  uniqueIndex('event_value_ordinal').on(t.eventId,t.category,t.key,t.ordinal),
  check('event_value_one_payload',sql`
    (${t.kind}='none' AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.entityId},${t.participantId})=0) OR
    (${t.kind}='bool' AND ${t.bool} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.entityId},${t.participantId})=1) OR
    (${t.kind}='int' AND ${t.int} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.entityId},${t.participantId})=1) OR
    (${t.kind}='decimal' AND ${t.decimal} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.entityId},${t.participantId})=1) OR
    (${t.kind}='text' AND ${t.text} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.entityId},${t.participantId})=1) OR
    (${t.kind}='instant' AND ${t.instant} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.entityId},${t.participantId})=1) OR
    (${t.kind}='entity' AND ${t.entityId} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.entityId},${t.participantId})=1) OR
    (${t.kind}='participant' AND ${t.participantId} IS NOT NULL AND num_nonnulls(${t.bool},${t.int},${t.decimal},${t.text},${t.instant},${t.entityId},${t.participantId})=1)
  `)]);
/** Complete before/after mutations replay entity, relationship, value and phase changes. */
export const eventMutations = bgwq.table('event_mutations', {
  id:id(),gameId:game(),eventId:uuid('event_id').notNull(),ordinal:integer('ordinal').notNull(),
  targetKind:text('target_kind').notNull(),targetId:uuid('target_id').notNull(),column:text('column_key').notNull(),
  operation:operationKind('operation').notNull(),
  beforeKind:valueKind('before_kind'),beforeBool:boolean('before_bool'),beforeInt:bigint('before_int',{mode:'bigint'}),
  beforeDecimal:numeric('before_decimal'),beforeText:text('before_text'),beforeInstant:timestamp('before_instant',{withTimezone:true}),
  beforeRef:uuid('before_ref'),
  afterKind:valueKind('after_kind'),afterBool:boolean('after_bool'),afterInt:bigint('after_int',{mode:'bigint'}),
  afterDecimal:numeric('after_decimal'),afterText:text('after_text'),afterInstant:timestamp('after_instant',{withTimezone:true}),
  afterRef:uuid('after_ref'),
},t=>[foreignKey({columns:[t.gameId,t.eventId],foreignColumns:[events.gameId,events.id]}),
  uniqueIndex('mutation_event_ordinal').on(t.eventId,t.ordinal),
  check('mutation_target_kind',sql`${t.targetKind} IN ('entity','link','field','phase','active_participant','clock','award','game')`)]);
/** Platform-trusted permanent rewards cannot be awarded by arbitrary user definition. */
export const awards = bgwq.table('awards', {
  gameId:game(),participantId:uuid('participant_id').notNull(),objectiveEntityId:uuid('objective_entity_id').notNull(),
  eventId:uuid('event_id').notNull(),points:bigint('points',{mode:'bigint'}).notNull(),
},t=>[primaryKey({columns:[t.gameId,t.participantId,t.objectiveEntityId]}),
  foreignKey({columns:[t.gameId,t.participantId],foreignColumns:[participants.gameId,participants.id]}),
  foreignKey({columns:[t.gameId,t.objectiveEntityId],foreignColumns:[gameEntities.gameId,gameEntities.id]}),
  foreignKey({columns:[t.gameId,t.eventId],foreignColumns:[events.gameId,events.id]}),
  check('award_points',sql`${t.points}>=0`)]);
export const ratings = bgwq.table('ratings', {
  userId:uuid('user_id').notNull().references(()=>authUsers.id),
  definitionId:uuid('definition_id').notNull().references(()=>definitions.id),
  rating:integer('rating').notNull().default(1200),games:integer('games').notNull().default(0),
  wins:integer('wins').notNull().default(0),draws:integer('draws').notNull().default(0),losses:integer('losses').notNull().default(0),
},t=>[primaryKey({columns:[t.userId,t.definitionId]}),
  check('rating_counts',sql`${t.games}=${t.wins}+${t.draws}+${t.losses}`),
  check('rating_nonnegative',sql`${t.games}>=0 AND ${t.wins}>=0 AND ${t.draws}>=0 AND ${t.losses}>=0 AND ${t.rating}>=0`)]);
```

## 2. PostgreSQL-only grants, triggers and private Broadcast

These are not a second source of table shape. They are the database-specific invariants that Drizzle's table DSL does not replace. They are applied after the generated schema with reviewable migrations.

```sql
-- PostgreSQL-only invariants not representable by Drizzle table declarations.
-- Apply AFTER the Drizzle-generated schema migration; review before production deployment.
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
  v_id := CASE WHEN TG_OP = 'DELETE' THEN OLD.version_id ELSE NEW.version_id END;
  IF EXISTS (SELECT 1 FROM bgwq.versions WHERE id = v_id AND published_at IS NOT NULL) THEN
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
CREATE TRIGGER immutable_event BEFORE UPDATE OR DELETE ON bgwq.events
FOR EACH ROW EXECUTE FUNCTION bgwq.reject_history_mutation();
CREATE TRIGGER immutable_event_values BEFORE UPDATE OR DELETE ON bgwq.event_values
FOR EACH ROW EXECUTE FUNCTION bgwq.reject_history_mutation();
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
CREATE TRIGGER game_requires_publication
BEFORE INSERT OR UPDATE OF version_id ON bgwq.games
FOR EACH ROW EXECUTE FUNCTION bgwq.assert_game_definition_published();

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
CREATE CONSTRAINT TRIGGER check_game_revision_history
AFTER INSERT OR UPDATE ON bgwq.games
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION bgwq.assert_game_event_parity();
CREATE CONSTRAINT TRIGGER check_event_revision_history
AFTER INSERT ON bgwq.events
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION bgwq.assert_game_event_parity();
```

