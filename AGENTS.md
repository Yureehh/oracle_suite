# Oracle repository instructions

## Before changing code

Read relevant architecture/domain documentation and inspect existing code. State
important assumptions and success criteria before substantial work. Ask the owner
before proceeding when requirements are ambiguous or a materially better approach
would change the agreed scope. Prefer the simplest complete solution, small cohesive
changes, and one verified vertical slice. Do not overwrite unrelated work, delete
unrelated untracked files, or replace working implementations without authorization.
Respect accepted ADRs; document a proposed change when revisiting them.

## Instruction scope

Codex discovers global instructions and files along the repository-root-to-working-
directory chain; deeper files take precedence. It does not automatically load every
nested file for a task started at the root. Before editing a subtree, explicitly
read the applicable nested files listed below, including instructions on intervening
paths. `AGENTS.override.md` takes precedence over `AGENTS.md` in the same directory;
configured fallback filenames and the instruction size limit also affect discovery.
See [official discovery guidance](https://developers.openai.com/codex/guides/agents-md/).

- `packages/python/oracle_core/AGENTS.md`
- `packages/python/oracle_arena/AGENTS.md`
- `packages/python/oracle_arena/src/oracle_arena/pokemon/AGENTS.md`
- `products/arena/pokemon/AGENTS.md` (also read for Pokémon code changes)
- `products/bets/AGENTS.md` and `products/lab/AGENTS.md`
- `apps/api/AGENTS.md`, `apps/web/AGENTS.md`, `apps/worker/AGENTS.md`

## Architecture

Keep domain boundaries clear and dependencies acyclic. Core must not depend on
Arena, Bets, Lab, or applications. Computational libraries must not depend on web
frameworks, UI components, or concrete databases without a demonstrated need.
Keep game-specific mechanics in their game domain. Share abstractions only when
actual consumers justify them. Keep CPU/GPU work out of synchronous API handlers.
Reuse compatible existing infrastructure; document why any new infrastructure
is needed. No generic plugin framework or speculative distributed system.
`products/` contains canonical product definitions; reusable code belongs in
`packages/python/`, and process entrypoints in `apps/`.

## Quality and evidence

Use type hints, explicit errors, and meaningful tests of behavior and edge cases.
Prefer deterministic, reproducible execution. Benchmark measured bottlenecks before
optimizing. Avoid unrelated reformatting, symbol renaming, and cleanup. Remove only
unused code introduced by your change. Keep documentation synchronized with actual
behavior. Distinguish implemented functionality, plans, research claims, and measured
results. Never fabricate implementation status, test outcomes, or benchmarks.

Run from the root before reporting substantial work complete:

```bash
uv sync --locked --all-packages
uv run --locked --all-packages ruff check .
uv run --locked --all-packages ruff format --check .
uv run --locked --all-packages mypy
uv run --locked --all-packages pytest
```

Add applicable workload tests and benchmarks when real functionality exists.

## Security and hygiene

Never commit or log credentials, tokens, or API keys. Use environment variables or
proper secret storage at application boundaries. Validate external inputs and respect
authorization boundaries. Public endpoints must not accidentally expose private
research data or artifacts. Keep generated datasets, checkpoints, databases and
runtime storage out of Git; keep small reviewed fixtures in package test directories.
Do not commit, push, publish, migrate Bets, or choose a license without authorization.

## Completion contract

For substantial tasks report what changed, why, relevant architectural decisions,
checks actually executed, known limitations, and remaining work. Name checks that
could not run and explain why. Keep trivial-change responses brief.

## Pokémon planning continuity

For Pokémon work, read `products/arena/pokemon/README.md`, its scoped instructions,
`docs/planning/pokemon/README.md`, the board and the selected epic card. The board is
canonical for task state; only owner acceptance moves In Review to Done. Current plan
creation approval does not authorize application implementation or Git publication.
