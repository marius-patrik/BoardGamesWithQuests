## Summary

<!-- State what was actually changed and which behavior remains unimplemented. -->

## Linked plan issue

<!-- Use a closing keyword to bind the approved Plan issue. -->
Closes #

## Changed areas

- [ ] `area:model` — Generic engine, JSON rules/quests
- [ ] `area:game` — Chess/checkers and exporters
- [ ] `area:server` — FastAPI/Supabase
- [ ] `area:web` — React frontend
- [ ] `area:desktop` — Tauri web wrapper
- [ ] `area:ci` — CI/DarkFactory
- [ ] `area:docs` — PRD/UML/README

## Verification evidence

- [ ] Changed interfaces, JSON schema, migrations, examples, docs, diagrams and deployment settings agree
- [ ] Every altered behavior has tests at the supported API/engine/browser/database boundary
- [ ] Tests assert successful outcomes, negative input, wrong identity, edge limits and shared-state races
- [ ] Real provider contract and browser integration are verified, not simulated by mocks
- [ ] Reviewed at least one regression that fails against the defective behavior
- [ ] Relevant actual product behavior exercised and results linked
- [ ] Required DarkFactory `quality` and `verify-bound-issue` checks pass
- [ ] Project-specific documentation and release checks pass
- [ ] User-authored game configuration remains JSON-only, never executable code
- [ ] Game neutrality, authorization, concurrency, security reviewed as applicable
- [ ] Active artifacts and Plan issue agree with implementation
- [ ] Final comprehensive behavior-suite requirements tracked by #239
- [ ] PR remains Draft until explicit maintainer approval; green structural checks alone do not establish playability
