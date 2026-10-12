# Agent Automation Architecture

This document records **durable automation design decisions**, not operational
instructions or run status. Operating rules belong in
[AGENTS.md](../AGENTS.md), current work in
[SCRATCHPAD.md](../SCRATCHPAD.md), and executable settings in
`.github/darkfactory.json` and the workflows themselves.

## Shared workflow boundary

Agent execution is owned by the shared
[DarkFactory](https://github.com/marius-patrik/DarkFactory) pipeline. The
repository owns a thin GitHub Actions caller, project configuration, and
explicitly supplied credentials. This avoids divergence between local copies
of orchestration and containers. The upstream commit pin is configured, not
repeated here.

## Harness independence

Coding-agent tools are declarative adapters rather than hard-coded branches
inside the pipeline. Each adapter describes a binary, arguments and a model
fallback chain. The runtime can advance to another available harness when one
is exhausted. Missing binaries or credentials do not invalidate the remaining
harnesses. A prior single-vendor runner could block delivery when that
provider's quota was exhausted; cross-harness fallback addresses that
architectural limitation.

Provider credentials are repository secrets explicitly forwarded across
called workflow boundaries; GitHub does not forward them automatically.

## Conversational lifecycle

Issues, plans, and pull requests form the tracked interaction surface.
Incoming requests are interpreted and confirmed, approved plans lead to work
on dedicated branches, and PR feedback drives revisions. Draft review and
merge gates are enforced through repository automation. The exact operational
requirements are specified in [AGENTS.md](../AGENTS.md).
