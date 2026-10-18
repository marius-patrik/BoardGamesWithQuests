---
status: published
---
# Native GitHub protection verification

`repo.dfconfig` declares the desired `main` policy: strict required checks, one independent approval, resolved conversations and protection against administrator bypass (`enforce_admins: true`). Only GitHub's actual settings enforce it; repository contents do not establish live compliance. Inspect the live settings with a repository administrator's GitHub CLI identity:

```bash
python3 .github/scripts/apply_branch_protection.py
```

The script is dry-run by default. An authorized administrator must inspect actual settings and apply the required policy via `--apply` (and separately opt into `--replace` if protection differs). GitHub's provider response, required check names, administrative enforcement and actual PR approval gate must be verified; no automation or source declaration substitutes for that evidence. The `develop`/release-only-`main` topology change is separately staged after existing reviewed PRs under [#348](https://github.com/marius-patrik/BoardGamesWithQuests/issues/348).
