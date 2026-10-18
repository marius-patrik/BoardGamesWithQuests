# Scratchpad — Active investigation

Temporary evidence only; promote verified facts to their canonical documents and remove obsolete notes.

- #271 is currently non-mergeable against #414 and must be synchronized **after** the local agent completes and the maintainer approves Phase 0.
- The implemented current-state #414 engine uses a standard 8×8 chess default board, `Move.validate()` hardcodes 8×8, and `GameManager.save_log()` is a stub; the recovered GUI and completed game behavior belong to #271.
- The last inspected Python 3.12 suite on #271 reported **424 passed, 46 skipped**, so actual Tkinter GUI acceptance remains unverified.
- The source packaging workflow prepares native artifacts but requires the finished `src/` UI from #271 before real platform artifact smoke tests can pass.
