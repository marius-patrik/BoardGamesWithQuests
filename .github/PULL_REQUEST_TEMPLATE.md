## Scope and acceptance

Describe **implemented** user-facing behavior on this PR's current head, link the owning issue, and state exclusions/risks. Unimplemented proposals belong in the owning GitHub issue, not in the PRD.

## Source ownership and documentation

- [ ] `src/` is the sole production Python package tree (no duplicate `packages/`).
- [ ] `.agents/PRD.md` and `.agents/AGENTS.md` describe verified product behavior/progress; root README and CONTRIBUTING symlinks are preserved.
- [ ] `docs/architecture/diagrams/` generated diagrams agree with Python source; `docs/reference/` original assets are unchanged.
- [ ] `python .github/scripts/validate_repository.py --check` and source diagram generation succeed; no old generated governance records were recreated.

## Verification

- [ ] Python 3.10–3.13 rule, persistence and package tests passed at the final SHA.
- [ ] Actual Tkinter controls and interaction paths tested, including rejected actions.
- [ ] Windows x64 PyInstaller artifact built and frozen GUI/persistence smoke passed.
- [ ] Source/docs site preview built and its real browser controls tested.
- [ ] CI failures, unavailable native checks and unresolved bugs recorded explicitly.

## Merge and release governance

- [ ] Source branch and target branch match repository promotion policy.
- [ ] Independent maintainer review covers the final commit and evidence.
- [ ] No direct release publication is inferred from a green CI run; distribution requires explicit approval.
- [ ] This PR remains unmerged until the maintainer authorizes integration.
