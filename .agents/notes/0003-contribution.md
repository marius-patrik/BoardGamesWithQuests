---
status: published
---
# Contribution and verification

Make one bounded, issue-linked, bot-authored PR per independently reviewable behavior; maintain explicit approval, external behavior tests and synchronized contracts. The existing #331 → #343 → #271 stack stays in review. The template's optional development-branch and tag/file release switch require an explicit, reviewed #350 decision; do not silently activate a conflicting policy.

```sh
python3 .github/scripts/generate_documents.py --write
python3 .github/scripts/generate_documents.py --check
python3 -m unittest discover -s .github/tests -p test_repository_structure.py
```

Builds and generated docs do not prove real Supabase/Vercel, two-browser play or release readiness.
