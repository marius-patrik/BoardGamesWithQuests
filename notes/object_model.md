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

### 4. Pluggable Rule Engine (Deviation — Not in the Reference Diagram)
- **Date**: 2026-10-02
- **Context**: The diagram specifies `RevizorTahu` as a fixed class whose internals implement `simulate_Move()`, `check_Šach()`, `check_Mat` and `check_Pat`. There is no rule registry, no notion of an enabled or disabled rule, and no extension point.
- **Deviation**: Rules become discrete, named, individually toggleable units held in a registry, and the validator evaluates the enabled set rather than hard-coding each rule.
- **Rationale**: FR-8 through FR-12 require that a custom rule be addable at runtime with no change to the engine core, and that any rule be disableable per game. Neither is expressible in the diagram's shape. Rank-relative rules (FR-13) also require deriving the home rank and castling files from a configured board, which the fixed-class shape has nowhere to express.
- **Mitigation**: `RevizorTahu` remains the validator and remains the diagram's class name. The rule units are composed by it rather than replacing it, so the diagram's box and its four documented operations still exist and still behave as drawn. The registry is an internal collaborator.
- **Approval**: Explicitly approved by the user on 2026-10-02 ("rules should be completely generalized, able to add custom ones and disable any for game").
