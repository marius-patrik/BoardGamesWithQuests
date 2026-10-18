# Plan

The single program scope, dependency graph and acceptance gates are maintained in [master issue #348](https://github.com/marius-patrik/BoardGamesWithQuests/issues/348).

1. Complete [#403](https://github.com/marius-patrik/BoardGamesWithQuests/issues/403): template-repo governance structure on PR #331.
2. Complete [#349](https://github.com/marius-patrik/BoardGamesWithQuests/issues/349): documentation/reference/source structure review.
3. Ratify the full product architecture together in [#350](https://github.com/marius-patrik/BoardGamesWithQuests/issues/350): API/schema/DSL/engine/client and outstanding release/branch decisions.
4. Finish #331 → #343 → #271, each with actual maintainer review and approval, on the existing stacked bases, and merge the finished stack into the current `main`.
5. After all three PRs are merged, separately authorize [#404](https://github.com/marius-patrik/BoardGamesWithQuests/issues/404): verify the fork-base SHA, rename the accumulated old `main` to `develop`, create the new `main` from that verified fork base, and migrate workflows, deployment triggers and protections.
6. Implement remaining issues as dependency-stacked, issue-bound bot PRs feeding into `develop`, each independently reviewed and merged only with maintainer approval.
7. Promote `develop` into the release `main` **only when explicitly requested separately by the maintainer**.

The G1 branching choice is accepted, but #404 has not been executed; release/version controller choice G2 is pending.
