# ADR 0001: Oracle monorepo foundation

- Status: Accepted for scaffold; workload and deployment choices remain provisional
- Date: 2026-10-12
- Sequence amendment: [ADR 0002](0002-pokemon-discovery-and-planning.md) places simulator compatibility research before durable Core implementation.

## Context

Oracle combines competitive game AI, predictive research, and cross-domain experiment
visibility. One developer must evolve it without duplicating engines or operating
premature infrastructure. Bets already exists independently and must be preserved.
The detailed Pokémon specification and first executable workload are still pending.

## Decision

Use one monorepo with Python-first reusable code and one eventual website. The owner
selected the existing `oracle_suite` directory as its root rather than nesting `oracle/`.
Use uv for packages, environments, dependency groups and a shared lockfile; use `src/`
packages with explicit ownership. Keep a non-distributable root development project
and only Core/Arena as initial libraries. Use Ruff, mypy and pytest with Python 3.12
as the checked baseline. Neither package depends on the other until a real use case.

Keep Core thin and domain mechanics specific. Products own specifications, applications
own process entrypoints, and libraries own reusable implementation. Provisional
Pokémon product branding does not define services. Bets stays external during this
bootstrap and Lab will consume existing workload results rather than duplicate them.

The uv_build backend supports the simple pure-Python layouts without custom build
configuration. Its compatible minor range lives in package build metadata; runtime
and dev dependencies are locked by uv. Build isolation may resolve build requirements
separately from the runtime lock, so release reproducibility will need explicit build
toolchain capture when publishing becomes a requirement.

## Alternatives

- Separate repositories: stronger dependency isolation but more coordination and
  duplicated conventions. Bets remains separate until an explicit integration plan.
- One package of scripts: less initial structure but unclear ownership as domains grow.
- A universal game framework: premature constraints before a second game reveals reuse.
- A service per provisional product: duplicates deployment and potentially evaluators.
- Other package managers: viable but unnecessary alongside the requested uv workflow.

## Consequences

Shared checks and documentation make development coherent, while package boundaries
keep computational logic independent of applications. One uv workspace requires
compatible Python/dependency constraints and does not enforce import isolation.
Two empty library shells are intentional installation boundaries, not evidence of
implemented infrastructure. The documentation footprint is larger than the code
because it records agreed constraints; avoid duplicating future specifications.

Monorepo ownership, Python-first development, uv, a thin Core and domain-specific
logic are established starting choices. FastAPI, Next.js, PostgreSQL, workers and
filesystem artifacts are preferences/candidates to revisit with the first workload.
Write a superseding ADR when requirements justify a material architectural change.

## Current naming

This record preserves the names used when accepted. [ADR 0003](0003-strixia-branding.md)
updates current branding and local paths; the architectural/domain decisions remain.
