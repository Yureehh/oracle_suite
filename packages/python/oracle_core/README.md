# Oracle Core

Core is the boundary for genuinely shared infrastructure. Today it is an installable
package shell with an import smoke test and no runtime dependencies or public contracts.
It is not a dumping ground for common-looking helpers.

Runs, workers, artifacts, configuration, persistence, model metadata and access control
are potential responsibilities only when real workloads justify them. Release 0 will
first define a durable execution slice. PostgreSQL, a Python worker and replaceable
artifact storage are provisional choices; none is implemented here.

Use the root [development commands](../../../docs/runbooks/local-development.md).
Core must not depend on Arena or applications. See the
[dependency boundaries](../../../docs/architecture/boundaries.md) and local `AGENTS.md`.
Open decisions include actual run semantics, adapter interfaces and the first concrete
consumers; avoid creating those contracts before their use case is defined.
