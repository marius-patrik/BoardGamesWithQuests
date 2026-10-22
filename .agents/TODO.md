# TODO — Outstanding v1.0.0 actions

The implementation order, exact steps and exit gates are in [PLAN](PLAN.md).

- [ ] Cross-check the recovered FIDE reference cases with independent complete-game/perft records and validate resulting clock/outcome/notation behavior.
- [ ] Extend English-draughts reference coverage to complete opening-to-terminal games and independent perft/variant interactions beyond the current short-king, multi-jump and crowning tests.
- [ ] Add missing non-square board, aggregate-budget and forced-effect-failure acceptance through the public revisioned action protocol.
- [ ] Mark `chess` and `english_draughts` definitions playable only after full end-to-end reference acceptance.
- [ ] Verify Tkinter clocks, expiration, game end, rewards, capture/promotion choice, reset, game switch and safe callback shutdown through obligatory Xvfb GUI acceptance.
- [ ] Complete player-facing chess and draughts notation exports; verify exported complete-game contents through the real UI.
- [ ] Extend preference and saved-game adversarial recovery across process restarts, symlink and path boundaries, oversized input and interrupted atomic writes.
- [ ] Verify the final frozen binaries on Windows x64, macOS ARM64/x64 and Linux x64: game actions, GUI, bundled JSON, installation diagnostic, persistence, exports, restart and checksums.
- [ ] Resolve current #271 review threads and any relevant archived #405 review issues with traceable fixes; validate generated docs and exact-head Python 3.10–3.13 CI.
- [ ] Obtain maintainer approval, merge #271 into `develop`, approve reviewed `develop → main` promotion and publish/verify gated v1.0.0.
