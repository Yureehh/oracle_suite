# Local-first deployment path

Nothing is provisioned. Local development uses uv and Python; Champions simulation
also needs Git and Node for the pinned engine. The local batch worker stores metadata
in SQLite and artifacts on disk. No container, web server, paid hosting or GPU is
required. See the [local batch runbook](../runbooks/local-batches.md).

The provisional service direction is:

```text
One website (Next.js) → API (FastAPI) → durable metadata (PostgreSQL)
                            ↓                    ↑
                      artifact storage ← Python worker
                                              ↓
                                     Agon / Pythia workloads
                                              ↓
                                  results consumed by Lyceum views
```

This diagram is conceptual. Its arrows do not specify a queue protocol or storage
schema. Local durable runs, recoverable claims, a worker and filesystem artifacts
already exist; an API and hosted deployment remain planned. PostgreSQL is a candidate
when a hosted workload needs shared metadata.
Persistence requires migrations, backup/restore tests and interruption recovery.

Begin with local processes and environment-driven application settings. Separate
request handling from CPU/GPU work. Prefer stateless API processes where practical;
durable runs must survive process restart. Keep resource requirements and scheduling
explicit when real workloads demand them.

When public hosting is needed, containerize actual entrypoints, use durable database
and artifact volumes, and add authentication/authorization before exposing private
runs. Move artifacts to object storage when filesystem deployment limits require it.
Workers can scale separately after measured contention demonstrates a need. Redis,
message brokers, Kubernetes and distributed GPU fleets are deferred.

Hosting provider and process placement are relatively reversible if packages stay
independent. Persisted run identifiers, state transitions, artifact references, API
contracts and provenance schemas are costly to change after historical data exists:
version them, define migration behavior, and validate failure semantics before use.
No provider is selected and no deployment workflow is configured.
