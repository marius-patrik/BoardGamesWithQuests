---
status: published
---
# Native GitHub protection verification

`repo.dfconfig` declares the intended `main` branch protection, but only GitHub's actual settings enforce it. Inspect the live settings with a repository administrator's GitHub CLI identity:

```bash
python3 .github/scripts/apply_branch_protection.py
```

The script is dry-run by default. Only use `--apply` after approval and after comparing the actual protection; divergent existing policies require an additional explicit `--replace`. PR review and required status checks must be verified against GitHub, not inferred from repository configuration.
