# Local durable Champions batches

PKA-012–014 implements a local batch of independent games. It is not Bo3 orchestration
or RL training. SQLite stores frozen inputs, run/attempt status and completed-game
manifests. Files store per-game public traces, seeds and submitted demonstration
choices. Runtime output lives under ignored `storage/local-runs/` by default.

## Run from the repository root

```bash
sh scripts/pokemon_foundation/prepare.sh --engine-only
uv sync --locked --all-packages
uv run --locked --all-packages python apps/worker/local.py submit --key demo-001 --games 8
```

Copy the returned run ID into the following commands, replacing `<run-id>`:

```bash
uv run --locked --all-packages python apps/worker/local.py work <run-id> --parallel 2
uv run --locked --all-packages python apps/worker/local.py status <run-id>
uv run --locked --all-packages python apps/worker/local.py resume <run-id> --parallel 2
```

`submit --teams /absolute/path/teams.json` accepts the native team schema in the
[battle guide](../planning/pokemon/foundation/005-adapter.md). The full teams are
engine-validated before the run is queued. `--seed 1,2,3,4` deterministically derives
a separate four-word seed per game. Repeating the submission key with identical inputs
returns the same run; changed inputs conflict. Use a new key for an intentional repeat.
Global `--storage` and `--showdown` options go before the subcommand.

One coordinator uses a bounded thread pool to drive independent Node game processes;
Node does mechanics, Python does orchestration. Defaults: eight games, two concurrent;
limits: 1–1000 games, 1–32 concurrent, 500 decision boundaries per game. Game execution
uses the labelled engine-default demonstration policy. It is not PKA-007's random
policy or a competitive baseline. There are no database writes per simulated turn.
Parallel completion order can differ; seeds and game IDs do not depend on scheduling.
Training throughput has not been benchmarked.

Ctrl-C stops admitting new games, lets current bounded games finish, then records
cancellation unless the batch has already completed. A forced process stop retains
previously committed games; use explicit `resume` after the coordinator has stopped.
Resume verifies artifacts and runtime provenance, then executes only missing game IDs.
A changed adapter, Python/Node version, reviewed npm lock or corrupt artifact stops
execution rather than silently changing the experiment. A succeeded run is terminal.
Expected engine errors fail the attempt visibly; corrected, unchanged runs may be
explicitly resumed. This local slice intentionally supersedes the design's earlier
new-run-only terminal retry proposal for failed/cancelled runs; attempt history remains.

## Storage and inspection

Core supplies concrete RunStore and Artifacts contracts; it imports no game domain.
A local OS file lock prevents two coordinators owning the same run. Atomic SQLite
claims and monotonic attempts fence stale publication. Each artifact is written and
synced before its completed-game manifest is committed. A crash can leave an orphan
file or repeat unfinished computation, but it cannot make a partial game look complete.
Local publication uses same-filesystem hard links without overwriting an existing file.
Supported platforms are macOS/Linux; this worker uses fcntl and is not Windows-tested.

```bash
uv run --locked --all-packages python apps/worker/local.py export --output /absolute/path/new-export.json
```

Export is versioned JSON of configurations, runs, attempts and completed-game manifests.
It refuses to overwrite an existing file. RunStore.backup creates a new SQLite backup;
neither command copies artifacts. Retain the artifact tree alongside the metadata.
The schema is version 1; newer versions are rejected. Future schema changes need an
explicit migration. Export supports a later migration path; PostgreSQL/Aurora support
and an import tool are not implemented or promised as a connection-string change.

Metadata, team allocations and seeds are private operator data, not policy observations.
Do not place the local storage directory on a shared network filesystem or expose it
through a public API. Shared multi-host claims/failover and mid-turn recovery are tracked
in [PKA-066 and PKA-065](../planning/pokemon/epics/e03.md#pka-065), respectively.

## Verification

Root tests include bounded concurrent execution, cancellation/resume, out-of-order
progress, lock contention, engine failure, artifact corruption, an actual killed
coordinator followed by resume, and a three-game real-engine batch. Core tests cover
claim races, stale attempts, duplicate publication, attempt history, backup/export,
unsupported schemas and interrupted artifact writes. Run the root development checks.

Recorded on 2026-10-13: locked workspace sync, Ruff lint/format, mypy (17 files),
all 46 repository tests without skips, bridge syntax and Markdown/task checks passed.
Both distributions built and an isolated environment completed an action-menu-driven
battle plus durable result/artifact verification. A CLI batch of six games completed
with three concurrent engines and out-of-order publication. These are correctness
checks, not a measured RL throughput benchmark or independent game-fidelity validation.

Implementation commits: `8389d2e` (storage), `3a56c36` (paired choices), `693bd8e`
(worker). Full local review run `20261013-221827-96c07d9e` completed with no remaining
findings after the saved-lock-digest regression was fixed and independently checked.
Cross-model review was unavailable; the independent local adversarial review ran.
Cards remain In Review; this delivery was committed locally, not pushed or merged.
