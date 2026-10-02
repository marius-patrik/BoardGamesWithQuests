# Object Model Reference & Conformance Notes

## Reference Architecture Diagram
The source of truth for the project object model is defined at:
https://app.diagrams.net/#G19OY7iySOQWRAZDFKy1r-7tJKG_L-_Qn8#%7B%22pageId%22%3A%22C5RBs43oDa-KdzZeNtuy%22%7D

## Strict Conformance Requirement
The object model in the codebase must strictly match the reference diagram. 
Any structural, behavioral, or naming deviation from this diagram must:
1. Be explicitly proposed to and approved by the user before implementation.
2. Be recorded and documented in this notes file with the rationale, date, and user approval context.

---

## Registered Deviations & Clarifications

### 1. Language and Translation Policy (Not a Deviation)
- **Policy**: Naming and language translations between the Czech reference diagram and the English codebase (e.g. `Figurka` -> `Piece`, `HerníPlocha` -> `Board`, `Tah` -> `Move`, `RevizorTahu` -> `MoveValidator`, `Hra` -> `GameManager`, `Hrac` -> `Player`, `Uzivatel` -> `User`, `vyhozene_figurky` -> `captured_pieces`, `zacni_tah` -> `start_turn`, etc.) are canonical design standards and do NOT constitute architecture or object model deviations.
- **English is canonical**: All code, class names, method names, attributes, variables, comments, and docstrings are written in English. Czech identifiers do not replace English ones.
- **Czech aliases are permitted**: The classes the diagram names in Czech additionally expose a Czech alias binding to the same object, so the diagram-to-code mapping stays discoverable from the source and the generated documentation. Aliases use ASCII spellings without diacritics (`HerniPlocha`, `Kun`, `Kral`, `Dama`, `Strelec`, `Pesak`, `Vez`). Comments, docstrings, commit messages and documentation remain English.
- **Amendment**: The clause "with no Czech identifiers or aliases" was removed on 2026-10-02. It contradicted the approved Czech-alias requirement and the pre-existing `Tower = Rook` / `Knight = Horse` aliases. English remains canonical; only the blanket ban on aliases is withdrawn.
- **Approval**: Explicitly clarified and approved by the user, and re-approved for the alias allowance on 2026-10-02.

### 2. Move Validation Architecture (Lazy Core + Aggregator)
- **Date**: 2026-09-04
- **Context**: Box 34 in the reference diagram raised the question of whether move validation should be precomputed eagerly for all pieces on turn start or computed on-demand upon clicking a specific piece.
- **Resolution**: Implemented on-demand validation (`get_valid_moves(piece, board)`) for user clicks/UI highlights, and an aggregator method (`get_all_valid_moves(player, board)`) on `MoveValidator` for checkmate/stalemate game-state evaluations.
- **Approval**: User agreed in planning discussion.

### 3. Settings Layer (Deviation — Not in the Reference Diagram)
- **Date**: 2026-10-02
- **Context**: The reference diagram defines no settings layer. `GUI_mockup.svg` — the visual reference for the game view — requires a SETTINGS tab and states explicitly: *"No SettingsView or SettingsController"* and *"No Settings model/controller/view exists yet."* The mockup also binds every settings row to a current data source (`board.py:26-37`, `piece.py:43-67`, `quest.py:9`, `timer.py:9`), which is only possible against real code.
- **Deviation**: `SettingsView`, `SettingsController` and a settings model are added to the view and controller layers. They have no counterpart in any diagram box.
- **Rationale**: FR-1 to FR-8 and FR-31 to FR-37 require the board, pieces, quests, clocks and rule sets to be configurable, and FR-7 requires rule logic to be authored. Without a settings layer those requirements are unreachable, and the mockup's configuration surface — the product's primary purpose — cannot be delivered.
- **Mitigation**: The settings classes are kept as thin adapters over the model. They hold no game state and add no rules of their own, so the deviation is additive and does not alter the object model the diagram defines.
- **Approval**: Explicitly approved by the user on 2026-10-02 ("yup 2 build it, note deviation").

### 3a. Named Configurations — Superseded by Sections 5 and 6
- **Date**: 2026-10-02
- **Context**: Rule sets became named, persisted profiles on 2026-10-02, later superseded by section 5: a `RuleSet` is a multiselect over `Rule` instances, `OrthodoxChess` is the default and cannot be edited, and rules and rule sets are files under `rules/` and `rulesets/` at the repository root. Kept as the question that was asked and answered.
- **Question**: does a named, persisted profile have a home in the diagram?
- **Assessment**: No box in either page describes a profile, and a profile is a saved configuration rather than game state, so it does not belong to `Hra` / `GameManager`.
- **Conclusion, as first reached**: not a separate deviation, because a profile belonged to the settings surface under deviation 3.
- **Superseded 2026-10-02**: the profile grew into a full configuration — board, pieces, rules, quests, clocks — and became a directory under `games/` rather than a file. It is therefore covered by sections 5 and 6 instead. Kept because the question of *where* a named configuration lives was genuinely open and the intermediate answer is part of the reasoning.
- **Approval**: Confirmed by the user on 2026-10-02 ("rule is one setting ruleset is full profile").

### 4. Customisable Rules and Quests — Data Alone Is NOT a Deviation
- **Date**: 2026-10-02
- **Assessment, as first reached**: The user raised the question directly: *"I dont think the diagram really supports that even tho it is a part of the assignment for rules to be customizable."* On examination the diagram's *fields* support it: `Tah.typ tahu` carries a move type, `Figurka.vektory` makes piece behaviour data, `GameManager.get_stav()` decides the outcome.
- **Superseded 2026-10-02**: that assessment covered *data-driven* customisation. Full customisation "in any way" — including a piece that may move to any square — turned out to need code, so `Rule` and `Quest` became parent classes with subclasses. That is deviation 5, not this section. What survives here is narrower and still true: **no deviation is needed for the data itself.** Board dimensions, piece vectors, clocks and rule values are all fields the diagram already draws.
- **Why the diagram already supports it**:
  - `Tah` carries `typ tahu: string`. That field is a move-type tag, so castling, en passant and promotion are expressed as move types generated and validated through the ordinary path, not as branches in the validator.
  - `Figurka` carries `vektory`, `vektory_utoku` and `skok` as data. Custom piece behaviour is therefore already diagram-shaped, and the classic pieces are simply the default values of those fields.
  - `RevizorTahu` exposes exactly four operations — `simulate_Move()`, `check_Šach()`, `check_Mat` and `check_Pat` — none of which is a special move. Special moves were never the validator's concern.
  - `GameManager.get_stav()` is the single point at which the game's outcome is decided, which is where draw conditions belong.
- **Consequence**: the rule set is configuration data held by the game, with standard chess as the default. Disabling a rule sets a value; no rule logic is removed from the source. Quest completion conditions are likewise data, so a quest is built from the settings surface rather than from a Python lambda.
- **A withdrawn proposal**: an earlier draft recorded deviation 4, "Pluggable Rule Engine", on the basis that runtime injection needs an extension point the diagram has no box for. Withdrawn, then partly reinstated by a different route — extension by subclassing a parent the diagram already draws, rather than by a registry.
- **Approval**: Confirmed by the user on 2026-10-02 — *"everything level 1 now and pluggable later"*, *"define logic actual quests data driven and settings configurable pluggable logic deffered"*.

### 5. Rule, Quest and the Configuration Concept (Deviation — Not in the Reference Diagram)
- **Date**: 2026-10-02 (revised several times the same day; superseded text replaced each time)
- **Context**: the diagram draws `RevizorTahu` as a fixed class with four operations and no configuration surface, and draws `Quest` with `nazev`, `popis` and `validate() : bool` but **no condition and no parameters**. Neither has anywhere to record which rules are in force, at what values, with what board, pieces, quests or clocks.
- **Deviation**: adds the abstractions the configuration requires.
  - `Rule` — a parent class carrying a configured `value` and per-game `state`, with four overridable hooks that each default permissively. Concrete rules are its subclasses.
  - `Quest` — a parent class with subclasses for the built-in quests, declaring `when`, `parameters()`, `progress()`, and `validate() -> bool`.
  - A configuration concept — a named, persisted set of board, pieces, rules, quests and clocks, of which `chess` is the default and `checkers` the second.
- **Why this is mild rather than foreign**: the diagram already uses this idiom. It contains a generalization edge `Kůň → Figurka`, with `Figurka` drawn as the parent carrying `název`, `vektory`, `vektory_utoku` and `barva`. One parent class per concept, with concrete variants as subclasses, is the diagram's own design.
  - *Caveat recorded for honesty*: the sketch is inconsistent. Only `Kůň` is explicitly connected to `Figurka`; the other five pieces are siblings that each redeclare `vektor`, `vektor_utoku` and `skok` instead of inheriting. The intent is clear even though the drawing is not.
- **`Quest.validate() -> bool` matches the drawing exactly**, because quest logic lives in the `Quest` subclass rather than in a separate condition object that would have needed the signature to change. There is no condition class.
- **Why four rule hooks is complete**: in a turn-based game, logic can only forbid a move or end the game. `permits_move` and `available_moves` cover the first, `outcome` the second, and `on_move_made` the bookkeeping the other two depend on. Chess rules, checkers rules, and logic well beyond both all map onto these.
- **Mitigation**: `RevizorTahu` is retained with all four drawn operations unchanged and *asks* the active rule set rather than embedding rule logic. Under the default configuration the game behaves exactly as the drawn model describes.
- **Deliberately not added**: a registration function such as `define_ruleset`, a rule registry, or `CustomBoard` / `CustomPiece` / `CustomQuest` types.
  - A registry is unnecessary because a configuration is composed explicitly, so the set of rule types is closed and greppable. A new rule is a new file plus one reference.
  - `CustomBoard` and `CustomPiece` would wrap data that is *already* custom. Board dimensions and piece vectors are data; new *behaviour* is expressed by a `Rule` subclass, which is the pattern already in use.
- **Fallback**: if a stricter reading is preferred, the same values can be held as plain data attributes on `GameManager` with no new classes, at the cost of the `Rule` and `Quest` hierarchies.
- **Approval**: Directed by the user across 2026-10-02, most explicitly *"we should generalize the configuration pattern across the whole engine"* and *"I agree with what you said before btw - drop the conditions for quests"*.

### 6. Configurations Live Outside the Package (Deviation — Not in the Reference Diagram)
- **Date**: 2026-10-02
- **Context**: the diagram describes classes and their members. It says nothing about *where* the concrete implementations live, and it draws each game concept as its own class rather than as a bundle.
- **Deviation**: concrete implementations are grouped into configuration directories under `games/` — `games/chess/` and `games/checkers/` — each holding board, `pieces/`, `rules/`, `quests/` and `clocks/`. The engine retains only the parent classes and the shared machinery.
- **Rationale**: it makes a configuration a copyable unit, which is what makes duplication the extension mechanism, and it keeps the diagram's classes where a reviewer expects to find them — one parent per concept, with variants beside it rather than scattered through the engine.
- **Mitigation**: the engine's public surface is unchanged in substance. `Figurka` is still the parent of the six pieces; only the location of the subclasses moves. A configuration is importable by path, so nothing about how a piece is used changes.
- **Consequence recorded**: a configuration is a bundle, so the diagram's classes are not one-to-one with directories. The mapping is documented in `PRD.md` section 6.
- **Approval**: Directed by the user on 2026-10-02 — *"make the top level layout controller/ model/ view/ and then just rulesets/ ... call the classic one chess"*.

### 7. Piece Symbols and the Absence of a Special King (Clarification — Not a Deviation)
- **Date**: 2026-10-02
- **Question**: should the engine hold a table mapping piece types to display characters and to FEN letters, and should it treat a "king" as a special piece type?
- **Assessment**: neither is required, and both would contradict the diagram's own generalisation.
  - **Symbols are data.** Every piece declares its own white and black unicode glyphs. The renderer and the notation writer therefore hold no knowledge of piece types at all, which also removes the existing behaviour where an unrecognised type silently serialised as a pawn.
  - **FEN characters are optional data.** A piece declares an FEN character or it has no FEN representation. Whether a position has a king is a *rule* — a configuration that has kings includes the check and checkmate rules — rather than a lookup by type name.
- **Why this is not a deviation**: `Figurka` in the diagram carries `název` and colour as attributes. Declaring its display symbols alongside them is extending an attribute list, not introducing a new structural relationship. The engine removing its own `getType() == "king"` coupling is the diagram's inheritance being used rather than bypassed.
- **Approval**: Directed by the user on 2026-10-02 — *"for pieces we should use unicode icons declared with the rest of the data"*, and the checkers requirement, which cannot be built while a king is hard-coded.
