# Local-first deployment path

Nothing is provisioned. Development currently needs uv and Python only; there is
no database, container, web server, paid hosting, or GPU prerequisite.

The provisional service direction is:

```text
One website (Next.js) → API (FastAPI) → durable metadata (PostgreSQL)
                            ↓                    ↑
                      artifact storage ← Python worker
                                              ↓
                                     Arena / Bets workloads
                                              ↓
                                  results consumed by Lab views
```

This diagram is conceptual. Its arrows do not specify a queue protocol or storage
schema. The first useful deployment decision should follow the Release 0 workload:
a durable run state machine, API, worker, recoverable task claims and artifacts.
PostgreSQL and a local filesystem artifact store are candidates for that slice.
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
