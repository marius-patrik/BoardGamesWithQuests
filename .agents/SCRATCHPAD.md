# Execution Workspace

This file holds only unfinished work. Source contracts are maintained in the
product requirements and the proposed comprehensive contract branch until
architectural decisions are ratified.

- Design and approve the final authoritative Supabase ERD in issue #289.
- Complete the Python engine's game-neutral JSON rules and actual public action
  boundary without reintroducing hardcoded Python game packages.
- Implement registered/anonymous player identity and the durable two-player
  create/join/act/history API; the FastAPI health bootstrap is not gameplay.
- Build the actual React game, account, settings and quest interfaces. The web
  bootstrap renders a shell only.
- Complete production Vercel project settings/secrets and test both deployment
  paths against the existing web/API projects.
- Reconcile the hosted project's migration ledger before any approved
  `supabase db push`; preserve unrelated accounts and Auth identities.
- Add native mobile signing/provisioning to produce real installable iOS IPA
  and signed Android packages; independently verify the generated artifacts.
- Complete official chess and draughts JSON definitions, behavior tests,
  accessible browser play and two-client public acceptance.
- Update the generated architecture diagrams and reference documents with every
  accepted change; do not treat a docs build as product proof.
