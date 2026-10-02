# Object Model Reference & Conformance Notes

The governing object model is the reference architecture diagram. Deviations from
it are recorded here with their rationale and approval context, as Rule 3
requires.

## Reference Architecture Diagram

https://app.diagrams.net/#G19OY7iySOQWRAZDFKy1r-7tJKG_L-_Qn8#%7B%22pageId%22%3A%22C5RBs43oDa-KdzZeNtuy%22%7D

- **File**: `Šachy - diagram tříd.drawio`
- **Pages**: `Page-1` — the full object model, and `MVC - GameView` — the MVC integration and view bindings.

**Status of this diagram**: it is the assignment specification. Anything it
defines is implemented; anything it does not define is out of scope unless a
user request adds it.

---

## Registered Deviations

### 1. Language and Translation Policy

- **Not a deviation.** Naming and language translation between the Czech diagram
  and the English codebase — `Figurka` → `Piece`, `HerníPlocha` → `Board`,
  `Tah` → `Move`, `RevizorTahu` → `MoveValidator`, `Hrac` → `Player`,
  `Uzivatel` → `User`, `vyhozene_figurky` → `captured_pieces`,
  `zacni_tah` → `start_turn` and the rest — are canonical design standards and
  do not constitute architecture or object model deviations.
- **English is canonical.** All code, class names, method names, attributes,
  variables, comments and docstrings are written in English.
- **Czech aliases are permitted.** The classes the diagram names in Czech
  additionally expose a Czech alias bound to the same object, so the
  diagram-to-code mapping is discoverable from the source and the generated
  documentation. Aliases use ASCII spellings without diacritics:
  `HerniPlocha`, `Kun`, `Kral`, `Dama`, `Strelec`, `Pesak`, `Vez`. Comments,
  docstrings, commit messages and documentation remain English.
- **Approval**: recorded with user approval, and re-approved for the alias
  allowance on 2026-10-02.

### 2. Move Validation Architecture — Lazy Core and Aggregator

- **Date**: 2026-09-04
- **Context**: Box 34 raised whether move validation should be precomputed for
  every piece at turn start, or computed on demand when a piece is clicked.
- **Resolution**: on-demand validation (`get_valid_moves(piece, board)`) for
  clicks and UI highlights, plus an aggregator (`get_all_valid_moves(player,
  board)`) on `MoveValidator` for checkmate and stalemate evaluation.
- **Approval**: recorded with user approval, 2026-09-04.

### 3. Settings Layer

- **Date**: 2026-10-02
- **Context**: the diagram defines no settings layer. `GUI_mockup.svg` requires a
  SETTINGS tab and states *"No SettingsView or SettingsController"* and *"No
  Settings model/controller/view exists yet."*
- **Deviation**: `SettingsView`, `SettingsController` and a settings model are
  added to the view and controller layers. They have no counterpart in any
  diagram box.
- **Rationale**: the board, pieces, rules, quests and clocks must be
  configurable, and rule logic must be authored. Without a settings layer none
  of that is reachable, and the mockup's configuration surface — the product's
  primary purpose — cannot be delivered.
- **Mitigation**: the settings classes are thin adapters over the model. They
  hold no game state and add no rules, so the deviation is additive and does not
  alter the object model the diagram defines.
- **Approval**: recorded with explicit user approval, 2026-10-02.

### 4. Rule, Quest, and the Configuration Concept

- **Date**: 2026-10-02
- **Context**: the diagram draws `RevizorTahu` as a fixed class with four
  operations and no configuration surface, and draws `Quest` with `nazev`,
  `popis` and `validate() : bool` but no condition and no parameters. Neither
  has anywhere to record which rules are in force, at what values, with what
  board, pieces, quests or clocks.
- **Deviation**, four things the diagram does not draw:
  - `Rule` — a parent class carrying a configured `value` and per-game `state`,
    with five hooks: `permits_move`, `available_moves`, `outcome`,
    `on_move_made`, `status`, each defaulting permissively. Concrete rules are
    its subclasses.
  - `Quest` — a parent class with subclasses for the built-in quests, declaring
    `when`, `parameters()`, `progress()`, and `validate() -> bool`.
  - A configuration — a named, persisted bundle of board, pieces, rules, quests
    and clocks. `chess` is the default; `checkers` is the second.
  - `ExportWriter` subclasses, one per format, per configuration.
- **Why this is mild rather than foreign**: the diagram already uses this idiom.
  It contains a generalization edge `Kůň → Figurka`, with `Figurka` drawn as the
  parent carrying `název`, `vektory`, `vektory_utoku` and `barva`. One parent
  class per concept with concrete variants as subclasses is the diagram's own
  design, and the generalization is applied to rules and quests.
  - *Recorded for honesty*: the sketch is internally inconsistent. Only `Kůň` is
    explicitly connected to `Figurka`; the other five pieces are siblings that
    each redeclare `vektor`, `vektor_utoku` and `skok` rather than inheriting.
    The intent is unambiguous even though the drawing is not.
- **`Quest.validate() -> bool` matches the drawing exactly**, because quest logic
  lives in the `Quest` subclass rather than in a separate condition object, which
  would have forced the signature to change. There is no condition class.
- **Why the rule hooks are complete for game logic**: in a turn-based game, logic
  can only forbid a move or end the game. `permits_move` and `available_moves`
  cover the first, `outcome` the second, and `on_move_made` the bookkeeping the
  other two depend on. Chess rules, checkers rules, and logic well beyond both
  all map onto these. `status` is display, not logic: it reports something worth
  showing, such as `Check`, while the game continues.
- **Mitigation**: `RevizorTahu` is retained with all four drawn operations
  unchanged and *asks* the active rule set rather than embedding rule logic.
  Under the default configuration the game behaves exactly as the drawn model
  describes.
- **Deliberately not added**: a registration function such as `define_ruleset`, a
  rule registry, or `CustomBoard` / `CustomPiece` / `CustomQuest` types. A
  configuration is composed explicitly, so the set of rule types is closed and
  greppable, and a new rule is a new file plus one reference. The `Custom*` types
  would wrap data that is *already* custom — board dimensions and piece vectors
  are data, and new behaviour is expressed by a `Rule` subclass.
- **Fallback**, recorded so the trade-off stays visible: if a stricter reading is
  preferred, the same values can be held as plain data attributes on
  `GameManager` with no new classes, at the cost of the `Rule` and `Quest`
  hierarchies.
- **Approval**: recorded with explicit user approval, 2026-10-02, most explicitly
  *"we should generalize the configuration pattern across the whole engine"* and
  *"drop the conditions for quests"*.

### 5. Configurations Live Outside the Package

- **Date**: 2026-10-02
- **Context**: the diagram describes classes and their members. It does not say
  where concrete implementations live, and it draws each game concept as its own
  class rather than as a bundle.
- **Deviation**: concrete implementations are grouped into configuration
  directories under `games/` — `games/chess/` and `games/checkers/` — each
  holding `board.py`, `pieces/`, `rules/`, `quests/`, `clocks/` and `export/`.
  The engine retains only the parent classes and the shared machinery.
- **Rationale**: it makes a configuration a copyable unit, so duplication is the
  extension mechanism, and it keeps the diagram's classes findable — one parent
  per concept, with variants beside it rather than scattered through the engine.
- **Mitigation**: the engine's public surface is unchanged in substance.
  `Figurka` is still the parent of the six pieces; only the location of the
  subclasses moves, and a configuration is importable by path, so nothing about
  how a piece is used changes.
- **Consequence recorded**: a configuration is a bundle, so the diagram's classes
  are not one-to-one with directories. The mapping is documented in `PRD.md`
  section 6.
- **Approval**: recorded with explicit user approval, 2026-10-02.

### 6. Piece Symbols and the Absence of a Special King

- **Clarification, not a deviation.**
- **Question**: should the engine hold a table mapping piece types to display
  characters and to FEN letters, and should it treat a "king" as a special piece
  type?
- **Assessment**: neither is required, and both would contradict the diagram's
  own generalisation.
  - **Symbols are data.** Every piece declares its own white and black unicode
    glyphs, so the renderer and the notation writer hold no knowledge of piece
    types at all. This also removes the behaviour where an unrecognised type
    silently serialised as a pawn.
  - **FEN characters are optional data.** A piece declares an FEN character or it
    has no FEN representation. Whether a position has a king is a *rule* — a
    configuration that has kings includes the check and checkmate rules — not a
    lookup by type name.
- **Why this is not a deviation**: `Figurka` carries `název` and colour as
  attributes, so declaring display symbols alongside them extends an attribute
  list rather than introducing a structural relationship. The engine removing
  its own `getType() == "king"` coupling is the diagram's inheritance being used
  rather than bypassed.
- **Approval**: recorded with explicit user approval, 2026-10-02 — *"for pieces we should use
  unicode icons declared with the rest of the data"* — and the checkers
  requirement, which cannot be built while a king is hard-coded.

---

## Non-Deviations Worth Stating

Recorded because the question is fair and the answer is not obvious.

- **Data-driven configuration needs no deviation.** Board dimensions, piece
  movement vectors, jump capability, clock values, rule values and quest
  parameters are all *fields* the diagram already draws: `HerníPlocha` holds the
  board, `Figurka` holds `vektory` and `vektory_utoku`, `Timer` holds the clock,
  `RevizorTahu` holds the validator. Only behaviour that cannot be expressed as a
  field needed a new abstraction, and that is section 4.
- **Special moves ride the ordinary move path.** `Tah` carries
  `typ tahu: string`, a move-type field the diagram draws. Castling, en passant
  and promotion are therefore move types generated and validated like any other,
  not branches in the validator.
- **FEN and PGN belong to chess, not the engine.** The diagram's export writers
  box enumerates the formats, so all are implemented — but FEN and PGN are
  chess formats and live in `games/chess/export/`. A game with no FEN
  representation has no FEN exporter, because the structure says so rather than
  a runtime capability check deciding.
- **Experience is derived, not stored.** The mockup shows quests carrying an XP
  reward, but `reward_points` appears on neither the diagram's `Quest` nor
  `Uzivatel`. `Uzivatel.splnene_kwesty: List(Kwest)` already holds the completed
  quests, so total experience is the sum of their rewards and `Uzivatel` gains no
  new field.
