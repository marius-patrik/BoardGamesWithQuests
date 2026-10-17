---
status: active
---
# Versioning and release discipline

- Keep the verified DarkFactory-controlled `pridever` release mode until an explicit approved #350 migration to template tags/file mode; never maintain parallel tag producers.
- Do not introduce an unapproved VERSION file or silent PR version bump.
- Create tags and GitHub Releases only from merged `main` commits; never move an existing tag. Verify the published release before claiming completion.
- Keep current reviewed native PR stack and protected main. Consider the template `development` gate in #350; repository declarations alone do not configure actual GitHub protection.


