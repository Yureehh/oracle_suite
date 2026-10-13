# Boundaries and dependencies

| Owner | Responsibility | Allowed direction once needed |
| --- | --- | --- |
| `oracle_core` | Narrow shared infrastructure and contracts | Standard library and justified infrastructure dependencies; no domains or apps |
| `oracle_arena` | Game-specific simulation, policies, training, evaluation | Core when a real consumer requires it; no apps or Bets |
| `products/` | Canonical domain/product definitions | Documentation links, no duplicate implementation |
| `apps/api` | Request validation and thin application orchestration | Domain libraries and selected adapters |
| `apps/worker` | Computational execution and job orchestration | Domain libraries and execution adapters |
| `apps/web` | Presentation and interaction | Public API contracts; no direct Python/package/database access |
| Lab (future views) | Cross-domain inspection of real research results | Existing result metadata and artifact references |

These are constraints for future code, not implemented dependency edges. There is
currently no Core/Arena dependency. Introduce workspace dependencies with uv workspace
sources only when needed; never rely on another member's accidentally installed
dependencies. uv workspaces share a lock and environment; they do not enforce import
boundaries. Review imports and test packages in isolation as behavior grows.

Separate environments, game rules, agent policies, training, and evaluation
conceptually; split files when code warrants it. Do not invent empty subpackages or
universal observation/action interfaces. Different games may need different methods.
Heavy training must execute outside synchronous API requests. Domain code should
remain usable from tests, CLI tools and workers without web framework imports.

Package runtime dependencies belong to package metadata. Optional training extras
can keep heavy ML stacks out of unrelated development. Conflicting dependency or
Python requirements may require independently managed environments rather than one
workspace. Bets dependency compatibility must be assessed before integration.

Application configuration and persistence adapters belong at process boundaries.
Add a storage contract to Core only when its real use case makes replacement useful.
Avoid generic repository/service layers around empty code.
