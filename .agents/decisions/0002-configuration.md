---
status: accepted
---
# Immutable game rules and persisted user preferences

## Trusted game data

Bundled `games/<identifier>/config.json` is loaded by the strict `load_bundled_definition` resource reader without importing individual game Python packages. The version-2 parser rejects duplicate keys, unknown fields, unsupported expressions and unbounded data. Frozen `GameDefinition` instances provide the immutable source for generic board/piece construction, rule hooks, state fields, clocks and configured quests.

`model.game.manager.GameManager` interprets only whitelisted, bounded declarative conditions, queries and effects; game identifiers do not select executable Python rule classes. Per-action work budgets bound geometric searches and condition evaluation. The same pinned definition is embedded in replayable canonical snapshots.

## User settings

`model.game.preferences` and `view.settings_dialog.SettingsDialog` permit players to set board square size (32–88 pixels) and visibility of coordinates. Persisted preferences contain only these fields. They are validated before writing, stored outside immutable game resources in the OS-specific application-data directory and atomically replaced. The UI exposes no rule or quest editing. Corrupted preference documents raise an error rather than being executed.
