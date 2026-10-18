---
status: published
---
# Contribution and verification

Make one bounded, issue-linked, bot-authored PR per independently reviewable behavior; maintain explicit approval, external behavior tests and synchronized contracts. Finish the existing #331 → #343 → #271 stack with maintainer-reviewed merges first. After its completion, issue #404 governs renaming old `main` to `develop` and establishing a new release `main` from a separately verified fork-base commit. New implementation then uses dependency-stacked bot-authored PRs targeting `develop`. Promotion to `main` requires a separate explicit maintainer request. The migration has not occurred; versioning/release mode remains a G2 decision in #350.

```sh
python3 .github/scripts/generate_documents.py --write
python3 .github/scripts/generate_documents.py --check
python3 -m unittest discover -s .github/tests -p test_repository_structure.py
```

Builds and generated docs do not prove real Supabase/Vercel, two-browser play or release readiness.
