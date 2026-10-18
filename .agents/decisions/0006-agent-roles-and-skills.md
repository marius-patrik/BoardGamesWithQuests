---
status: accepted
---
# Portable agent roles and skills

## Decision

Keep the five repository-local roles (orchestrator, planner, implementer, reviewer and verifier) in `.agents/agents/` and task-focused procedures in `.agents/skills/<name>/SKILL.md`. All roles inherit generated `.agents/AGENTS.md`; procedures supplement rather than override approved requirements, human review or security controls.

## Consequences

These Markdown records are portable guidance, not a competing agent runtime. They do not prove a particular execution provider has discovered, installed or invoked a role or skill. Review and verification require reproducible evidence before a maintainer authorizes merge.
