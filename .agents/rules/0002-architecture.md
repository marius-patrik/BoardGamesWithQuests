---
status: active
---
# Architecture and ownership

- Assign one canonical owner to each capability, data model and state transition. Refactor the owner rather than creating competing implementations.
- Prefer simple, cohesive, discoverable modules with descriptive names over generic `utils` or `misc` files.
- Separate core mechanisms from project- or provider-specific policies; configure differences instead of duplicating entire subsystems.
- Avoid unrequested compatibility shims, legacy fallbacks and transitional production paths. Delete obsolete implementations only after verifying their consumers and state.
- Record a material architecture change as an accepted decision and update relevant approved requirements when scope changes.

### BoardGamesWithQuests: Format and Source Quality
Use the repository's configured formatters and typecheckers. Format
changes must remain scoped to relevant files and must not replace real
behavior testing.

### BoardGamesWithQuests: No Disposable Production Implementations
Do not add or retain placeholder UIs, bootstrap-only endpoints, fake
health/readiness states, intermediate servers, throwaway CLIs or tests that
merely certify an unavailable feature. Only permanent supported behavior
belongs in a mergeable production path. Record unmet requirements as
blocked without manufacturing substitutes.

Use Python namespace packages for directories that need no executable
initialization; verify built distributions, import discovery and packaged
resource loading before removing initializers.
