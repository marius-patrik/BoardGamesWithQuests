# Object Model and Reference Mapping

The [provided diagrams](reference_diagram.md) remain requirements/reference
evidence, not mandatory duplicate runtime classes. The live implementation
diagrams are generated from Python source during documentation builds.

## Package ownership

| Concern | Implementation home |
|---|---|
| Generic game state, pieces, moves, validators, clocks and rule evaluation | `packages/server/engine/model/` |
| Game interaction coordination (`GameController`) and retained window controller | `packages/server/engine/controller/` |
| Public HTTP surface and identity/game routes | `packages/server/api/` |
| Managed PostgreSQL migrations and Supabase local configuration | `packages/server/supabase/` |
| Browser presentation and future game/settings views | `packages/web/` |
| Desktop and mobile shell of the same deployed website | `packages/native/` |

There is **no Python view package**, but the controller package remains.
`GameController` provides selection and move coordination; `WindowController`
is preserved legacy window-specific state and is not a production API boundary.
Serverless game commands will require authenticated, stateless orchestration
rather than retaining these mutable instances across requests.

 `GameView` and `PlayerView` describe
future React responsibilities, not new Python classes. The old chess/checkers
Python packages are not part of the server package tree. Reintroducing game
content requires declarative JSON and an agreed persistence/definition model,
not game-specific executable Python subclasses.

The retained engine modules have not yet been validated against the final
declarative engine requirements. Reference UML source remains unchanged,
and intended modern differences are resolved in the implementation contract.
Gameplay, Auth, concurrency, schema and export guarantees require actual
end-to-end verification rather than class inventories.
