---
name: implementation-verification
description: Implement a bounded correction and demonstrate player-observable behavior with independent evidence.
---
# Implementation Verification

## When to use

During a scoped product correction and before requesting review for v1.0.0.

## Procedure

1. Identify the actual existing implementation owner, affected user/consumer boundary, and reproducible observable defect. Do not redesign the whole engine or UI.
2. Check current `.github/tests/` acceptance coverage and independently sourced expected behavior; classify obsolete implementation-coupled tests as retain/adapt/replace/delete.
3. Write a **real boundary regression** that fails before the correction. Use the production `DesktopSession`, actual Tkinter user interaction or extracted frozen app as appropriate. Pure math/parser/security diagnostics may supplement but never replace it.
4. Make the smallest cohesive, readable correction. Remove obsolete/dead/duplicated code **after** reconciling consumers and replacing real behavioral coverage.
5. Run focused acceptance, then affected integration, Python-version and GUI/native gates as relevant. Do not interpret skipped mandatory checks as passed or use process survival as gameplay acceptance.
6. Inspect final diff and update authored current-state governance and generated documents together; avoid adding desired v2 design as if implemented.
7. Report starting/final SHA, exact files, reproduced failure, passing observable scenarios, commands/platforms, unrun or blocked checks and any unresolved risks.

## Evidence of completion

A reproducible source change and concrete final-head player/consumer acceptance evidence. No self-approval, unattended merge or release.

Inherit `.agents/AGENTS.md` and the v1 owner [#430](https://github.com/marius-patrik/BoardGamesWithQuests/issues/430).
