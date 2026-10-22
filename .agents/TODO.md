# TODO — Outstanding v1.0.0 actions

The implementation order, exact steps and exit gates are in [PLAN](PLAN.md).

- [ ] Port #405 chess reference rules through a real versioned game session: illegal/unsafe castling, en passant discovered check, promotion, draws, dead material, replay and complete games.
- [ ] Port English-draughts acceptance: compulsory and branching multi-jump captures, short kings, promotion continuation rules, terminal positions and complete games.
- [ ] Verify variant-independent board dimensions, bounded hook evaluation and failure atomicity through publicly supported action submission.
- [ ] Mark `chess` and `english_draughts` definitions playable only after full end-to-end reference acceptance.
- [ ] Verify Tkinter clocks, expiration, game end, rewards, capture/promotion choice, reset, game switch and safe callback shutdown through obligatory Xvfb GUI acceptance.
- [ ] Complete player-facing chess and draughts notation exports; verify exported complete-game contents through the real UI.
- [ ] Prove preference recovery, filesystem boundary protection and restart behavior under hostile input through desktop user paths.
- [ ] Verify the final frozen binaries on Windows x64, macOS ARM64/x64 and Linux x64: game actions, GUI, bundled JSON, installation diagnostic, persistence, exports, restart and checksums.
- [ ] Resolve current #271 review threads and any relevant archived #405 review issues with traceable fixes; validate generated docs and exact-head Python 3.10–3.13 CI.
- [ ] Obtain maintainer approval, merge #271 into `develop`, approve reviewed `develop → main` promotion and publish/verify gated v1.0.0.
