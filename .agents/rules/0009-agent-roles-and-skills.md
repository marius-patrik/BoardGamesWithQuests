---
status: active
---
# Agent roles and reusable skills

- Before selecting an agent role, inspect `.agents/agents/` and choose the smallest role that can own the task. The orchestrator coordinates and integrates; it does not replace independent verification.
- Load `.agents/AGENTS.md` as the governing ruleset. Role files refine responsibility and deliverables but never override owner approvals, security constraints or required checks.
- Select procedures from `.agents/skills/<name>/SKILL.md` according to their descriptions. Skills are instructions, not automatically installed executables or proof of runtime support.
- If dispatching independent work, define explicit inputs, output, scope, acceptance criteria and the integration owner. Do not claim delegation occurred unless actual agents ran.
- Review and verification roles report evidence and defects; neither role grants its own approval or makes an unverified merge claim.

### BoardGamesWithQuests: DarkFactory Integration
Use the installed DarkFactory-managed pipeline and `repo.dfconfig` as the
single authoritative DarkFactory configuration. Keep supported native
manifests when build tools require them. Do not maintain parallel workflow
implementations, duplicate credentials configuration or copies of shared
harness logic. Pin verified external workflow and action dependencies.
Do not delete native manifests until their generation/replacement passes
the actual consumer build and deployment checks.
