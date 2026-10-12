# Object Model — Approved Design Deviations

**Purpose:** Record deliberate differences between the [external reference diagram](reference_diagram.md) and the **target implementation**, with rationale and approval. This is not an inventory of completed code. The reference document alone owns the literal boxes, members, spelling errors and disagreements between its two pages; the [PRD](PRD.md) owns acceptance requirements; the [execution plan](../SCRATCHPAD.md) owns implementation status.

## Actual implementation

The generated [class and inheritance graph](diagrams/implementation-classes.svg) and [package dependency graph](diagrams/implementation.svg) are rendered from tracked Python on each documentation build. They show what exists on the checked-out revision, **not** whether target behaviors, edges or UML requirements are satisfied. In particular, `main` does not yet include the Tkinter `GameView` and `PlayerView` implementations, the game rules, or their integration tests.

## Approved deviations and design decisions

All entries below describe the **agreed target**, not necessarily completed functionality. Approval dates refer to the maintainer's design discussion; a feature should not be marked delivered before its code and behavior are verified.

| Decision | Target / difference from the reference | Rationale and approval |
|---|---|---|
| Naming and translation | English names are canonical; ASCII Czech aliases map to the **same** classes where required by [PRD §5](PRD.md#5-naming-requirements). | Translation is not structural deviation; alias policy approved 2026-10-02. |
| Validation (diagram's unresolved question) | Calculate legal destinations on selection; aggregate all legal moves for mate/stalemate evaluation. | Avoid exhaustive UI recalculation while keeping complete game-end evaluation. Approved 2026-09-04. |
| Configuration and packaging | Shared `packages/engine/`; independent `packages/chess/` and `packages/checkers/`, with game-local `config.json`, behavior extensions and entry-point discovery. No `src/games/`. | Copyable game packages without chess-specific behavior in the engine. Approved 2026-10-02; folder layout updated 2026-10-12 and present on `main`. |
| Rule model | `Rule` with configured values, per-game state, and `permits_move`, `available_moves`, `outcome`, `on_move_made`, `status` hooks. Active rules are explicitly composed. | The diagram has a fixed validator and no rule extension mechanism. Approved 2026-10-02. |
| Quest model | `Quest` subclasses expose validation and progress; `QuestManager` holds current-game quests, `User` holds completions, XP derives from completed rewards. No standalone condition class. | Supports configurable objectives while preserving the drawn `Quest` concept. Approved 2026-10-02. |
| Field declarations | `Field`/`Configurable.spec()` drives a shared form renderer for boards, pieces, clocks, rules and quests. | The reference lacks a settings schema. Approved 2026-10-02. |
| Settings UI | Dedicated settings view/controller adapt the model without owning game rules or persistent game state. | The GUI mockup requires configuration, which the reference does not depict. Approved 2026-10-02. |
| Piece symbols and king handling | Glyphs and optional FEN identifiers are per-piece configuration data; no engine-level king/pawn tests or fallback piece type. | Works for chess and checkers and custom pieces. Approved 2026-10-02. |
| Moves | `Move` retains its drawn start/end/type but additionally records ordered hops for a multi-capture turn. | Draughts chains are one logical move. Approved 2026-10-02. |
| Outcomes | A `Result` describes winner, ending reason and rule precedence; the drawn game-state accessor can derive its integer/status from the result. | One integer cannot resolve competing terminal rules. Approved 2026-10-02. |
| Clocks | `Timer` remains the running countdown; configurable `Clock` supplies initial time and increment. | Increment is absent from the sketch. Approved 2026-10-02. |
| Export hierarchy | An `ExportWriter` base has format-specific implementations hosted by the game that supports them. | **Not drawn as inheritance:** none of the three writer boxes is connected. User-directed 2026-10-02. |
| FEN import | Chess-specific reader alongside its writer, for round-trip verification. | The reference draws writers only. User-directed 2026-10-02. |
| User-authored rules/quests | Rule/quest modules are loaded from the selected configuration directory, with syntax validation and path boundaries. | Enables behavior beyond movement vectors. User-directed 2026-10-02. |

## Reference ambiguities (not additional deviations)

- `GameVeiw` reverses `e`/`i`; the target class is `GameView`. It is **not** missing an `r`. The reference's `HracView` is only a *type label*, not a class box; `PlayerView` is required by the intended UI.
- Page 1 models `hraci: List(Hrac)`; Page 2 uses `List(Uzivatele)`. The target keeps player instances associated with users, rather than replacing players with users. The two diagram pages do not literally agree.
- The only explicitly connected `Figurka` subclass is `Kůň`. Other piece-box relationships are incomplete, not proof of five distinct hierarchies.
- The `Extends` annotation is a loose label beside the pieces, not an inheritance edge for export writers.
- `ChessNotationWriter` lists formats in prose but has no related generalization; its presence specifies the export requirement, not the intended implementation shape.

Refer to [the diagram transcription](reference_diagram.md) for the exact boxes, typos and relationships. Do not re-copy that inventory here.

## Verification boundary

A deviation is **approved design** until the relevant feature PR is integrated and behavior-tested. Source-generated UML verifies current class relationships only. Full gameplay conformance and any claim of an executable release remain gated by the fresh behavioral test suite in [#239](https://github.com/marius-patrik/BoardGamesWithQuests/issues/239).
