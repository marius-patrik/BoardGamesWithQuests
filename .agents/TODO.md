# TODO — Current implementation queue

Detailed steps and acceptance are in [PLAN](PLAN.md). Do not mark unfinished runtime behavior as shipped.

- [ ] Inventory #405 JSON engine, rules, tests and server-only functionality against live #271/#422; record each disposition.
- [ ] Replace the old Python-loaded `GameManager` with the full #405 revisioned transition authority, adapting it to canonical `Board`/`Piece`/`Move` and the recovered read-only board/snapshot queries, outcome resolution, captures, effects and replay; prove first complete player-driven JSON transition before GUI migration.
- [ ] Complete validated chess and English-draughts JSON and action/clock/quest semantics.
- [ ] Migrate Tkinter session/controllers/views and permitted JSON settings; remove all rule/quest editing, executable user-authored Python and code-editor paths.
- [ ] Run real engine/GUI adversarial and complete-game acceptance across supported Python versions.
- [ ] Validate four native packaged executables from the implemented GUI; preserve disabled release until proven.
- [ ] Reconcile #271/archived #405 reviews, update source documentation/diagrams, independently review and seek approval.
- [ ] After approved #271 merge, verify protected promotion and v1.0.0 binaries; defer #422 until afterward.
