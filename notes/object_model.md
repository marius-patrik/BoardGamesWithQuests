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
- **Rationale**: FR-4, FR-5, FR-6 and FR-23 require the rule set, custom rules, quests and clocks to be configurable per game. Without a settings layer those requirements are unreachable, and the mockup's configuration surface — the product's primary purpose — cannot be delivered.
- **Mitigation**: The settings classes are kept as thin adapters over the model. They hold no game state and add no rules of their own, so the deviation is additive and does not alter the object model the diagram defines.
- **Approval**: Explicitly approved by the user on 2026-10-02 ("yup 2 build it, note deviation").

### 3a. Rule Set Profiles — Part of Deviation 3, Not a New One
- **Date**: 2026-10-02
- **Context**: Rule sets became named, persisted profiles on 2026-10-02: a rule is one setting with a value, a rule set is the full named profile of those settings, `Classic Chess` is the default and cannot be edited, and custom sets persist to a file on disk.
- **Question**: does a named, persisted profile have a home in the diagram?
- **Assessment**: No box in either page describes a profile, and a profile is a saved configuration rather than game state, so it does not belong to `Hra` / `GameManager`.
- **Conclusion**: not a separate deviation. A profile is part of the settings surface built under deviation 3 above, and is recorded here so the question was asked rather than assumed. Selecting which profile a game runs under is `GameManager`'s configuration, which the diagram already allows.
- **Approval**: Confirmed by the user on 2026-10-02 ("rule is one setting ruleset is full profile").

### 4. Customisable Rules and Quests — NOT a Deviation
- **Date**: 2026-10-02
- **Assessment**: The user raised the question directly: *"I dont think the diagram really supports that even tho it is a part of the assignment for rules to be customizable."* On examination it does, and no deviation is required.
- **Why the diagram already supports it**:
  - `Tah` carries `typ tahu: string`. That field is a move-type tag, so castling, en passant and promotion are expressed as move types generated and validated through the ordinary path, not as branches in the validator.
  - `Figurka` carries `vektory`, `vektory_utoku` and `skok` as data. Custom piece behaviour is therefore already diagram-shaped, and the classic pieces are simply the default values of those fields.
  - `RevizorTahu` exposes exactly four operations — `simulate_Move()`, `check_Šach()`, `check_Mat` and `check_Pat` — none of which is a special move. Special moves were never the validator's concern.
  - `GameManager.get_stav()` is the single point at which the game's outcome is decided, which is where draw conditions belong.
- **Consequence**: the rule set is configuration data held by the game, with standard chess as the default. Disabling a rule sets a value; no rule logic is removed from the source. Quest completion conditions are likewise data, so a quest is built from the settings surface rather than from a Python lambda.
- **A withdrawn proposal**: an earlier draft of this file recorded deviation 4, "Pluggable Rule Engine", on the basis that runtime rule injection needs an extension point the diagram has no box for. That proposal is withdrawn. The pluggable form is deferred to a separate master issue covering rules, board, pieces and quests, and is explicitly out of scope for the current track.
- **Approval**: Confirmed by the user on 2026-10-02 — *"everything level 1 now and pluggable later"*, *"define logic actual quests data driven and settings configurable pluggable logic deffered"*.

### 5. Rule and RuleSet (Deviation — Not in the Reference Diagram)
- **Date**: 2026-10-02 (revised twice on the same day; superseded text replaced)
- **Context**: FR-7 to FR-20 require that logic in this product be written in exactly one place. The diagram draws `RevizorTahu` as a fixed class with four operations (`simulate_Move()`, `check_Šach()`, `check_Mat`, `check_Pat`), two data fields (`herni_plocha`, `tah`) and no configuration surface. There is nowhere in either page to record *which rules are in force, at what values*.
- **Deviation**: adds two types the diagram does not draw.
  - `Rule` — a parent class carrying a configured `value` and per-game `state`, with four overridable hooks (`permits_move`, `available_moves`, `outcome`, `on_move_made`). Concrete rules such as castling, en passant and fifty-move are its subclasses.
  - `RuleSet` — a named multiselect over `Rule` instances. It holds no behaviour of its own.
  - `OrthodoxChess` — the default `RuleSet`, every rule at its orthodox value.
- **Why this is a mild deviation rather than a foreign structure**: the diagram already uses this idiom. It contains a generalization edge `Kůň → Figurka`, with `Figurka` drawn as the parent carrying `název`, `vektory`, `vektory_utoku` and `barva`. One parent class per concept, with concrete variants as subclasses, is the diagram's own design. Applying it to rules introduces no new *kind* of relationship.
  - *Caveat recorded for honesty*: the sketch is inconsistent. Only `Kůň` is explicitly connected to `Figurka`; the other five pieces are drawn as siblings that each redeclare `vektor`, `vektor_utoku` and `skok` instead of inheriting. The intent is clear even though the drawing is not.
- **Why four hooks is complete**: in a turn-based game, logic can only forbid a move or end the game. `permits_move` and `available_moves` cover the first; `outcome` covers the second; `on_move_made` covers bookkeeping the other two depend on. Every rule in `notes/chess_rules.md` maps onto these, and so does logic well beyond it — a piece that may move to any square, a piece that must capture if able, a game that ends when a named piece is lost.
- **Mitigation**: `RevizorTahu` is retained with all four of its drawn operations unchanged. It *asks* the active `RuleSet` rather than embedding rule logic, so the drawn box and its documented behaviour survive intact. Under `OrthodoxChess` the game behaves exactly as the drawn model describes, so no behaviour changes.
- **Deliberately not added**: a registration function such as `define_ruleset`, a rule registry, or `CustomBoard` / `CustomPiece` / `CustomQuest` types.
  - A registry is unnecessary because a rule set is constructed explicitly by multiselect, so the set of rule types is closed and greppable. A new rule is a new file plus one reference.
  - `CustomBoard` and `CustomPiece` would wrap data that is *already* custom. `Board(dimensions=(10, 10))` is a custom board; `Piece(name="Ferz", vectors=...)` is a custom piece. Classes that add nothing and exist only for symmetry were rejected.
- **Execution of authored code**: rules load only from the project's `rules/` directory, never from an arbitrary path or user input elsewhere, and the editor validates a rule before it joins the vocabulary. Recorded because running player-authored code is a deliberate product property and should be bounded rather than assumed.
- **Fallback**: if a stricter reading is preferred, the same values can be held as plain data attributes on `GameManager` with no new classes, at the cost of the `Rule` hierarchy. Recorded so the trade-off stays visible.
- **Approval**: Directed by the user across 2026-10-02 — *"maybe make it so the Rule class handless this so Rules are the only place thats logic (code) driven and not just data driven and that allows us to add any logic we want"*, and *"we need to figure out a clever way to support this"*.
