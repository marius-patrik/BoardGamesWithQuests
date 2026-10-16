-- Non-destructive bootstrap only; the authoritative data model requires approval.
-- No application tables or previous-project cleanup are defined by this migration.
create schema if not exists bgwq;
revoke all on schema bgwq from public, anon, authenticated;
