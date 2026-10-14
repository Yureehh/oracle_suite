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

## Recorded random-policy Bo3 sets

PKA-007/008/016 adds a separately versioned workload while preserving the original
independent engine-default batch. Submit a small batch of sets:

```bash
uv run --locked --all-packages python apps/worker/local.py submit --key bo3-demo-001 --sets 4
uv run --locked --all-packages python apps/worker/local.py work <run-id> --parallel 2
uv run --locked --all-packages python apps/worker/local.py status <run-id>
```

`--sets` and `--games` are mutually exclusive; omitting both retains the original
eight-game engine-default workload. Bounds: 1–333 sets, at most three games per set,
up to 32 concurrent engines. Games within a set are sequential; other sets can run
in parallel. Each game has a fresh ordered four-of-six preview and battle state,
using the same fixed six-member teams. Set `s` reserves game IDs `3*s` through
`3*s+2`; early stopping leaves unused IDs, not missing results.

Python samples uniformly over complete player-visible paired actions, including
preview, targets, switches and eligible Mega choices. Uniform menu sampling is not
a strategic baseline: it can switch frequently or choose legal but poor moves.
Per-player policy seeds are derived separately from the frozen engine seed; pool
scheduling does not change a game's decisions. Waiting does not consume a random draw.
Only the player whose visible request changed resamples after an unavailable choice.
Bridge rollback retains both players' prior request facts when a later submission
reveals the other player's restriction; bilateral trapping has a real-engine regression.
These actual submissions are recorded; after 16 retries or any ordinary engine error,
the game fails explicitly. No hidden-state legality probing or default fallback occurs.

Scoring mirrors the pinned Showdown server: at most three game slots, draws consume a
slot and lower the win threshold to `floor((3 - draws) / 2) + 1`. A threshold winner
ends the set early; otherwise three games with equal wins produce a tied set. This
is simulator-series behavior, not independently verified Champions tournament rules.
Timeouts, process errors and the 500-decision limit are failures, not draws or losses.

Each completed-game trace includes commands, policy seeds, rejected attempts, public
history and a frozen copy of prior games' public history. Earlier artifacts never
receive later evidence. The random agent does not infer spreads or adapt to that
history; transient battle state resets. Set scores/outcomes are reconstructed from
the immutable completed-game records and shown by `status`, including partial sets.
Controller artifacts, error messages and frozen teams remain private operator data.

Ctrl-C stops admitting games, allows active games to publish, then leaves unfinished
sets cancelled. Explicit `resume` retains completed games and their evidence, restarting
only an unfinished game from its seed. Old independent-game runs remain inspectable;
execution across a changed Agon version is rejected by existing provenance checks.
No metadata migration, mid-turn checkpoint, trainer or cloud service is introduced.

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

Recorded-set verification on 2026-10-14: all 68 repository tests passed, alongside
locked sync, Ruff lint/format, strict mypy (19 files), pre-commit and bridge syntax.
Tests include scoring/draw boundaries, cancellation and failure/resume, chronological
evidence isolation and single/bilateral trapping refresh. A CLI two-set batch succeeded;
four real sets produced byte-identical per-game artifacts at concurrency one and two.
Agon 0.5.0 built as source/wheel; a fresh isolated wheel ran a game and preserved
bilateral request reveals. Use a fresh/no-cache environment when retesting a wheel
rebuilt under the same unreleased version, to avoid a cached older build. These are
correctness checks on small compatibility teams, not RL throughput or strength claims.

Independent local review `20261014-105457-09a4c2b8` completed; its bilateral-request
rollback finding was fixed and independently verified. Cross-model transport was
unavailable. Follow-up checks cover peer-success drain after a parallel failure,
unchanged-request rejection and an actual killed set coordinator followed by resume.
An existing diagnostic limit remains: concurrent game failures retain the last
processed exception in the attempt's error field, not a complete list of causes.

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
Initial handoff kept cards In Review and commits local. On 2026-10-13 the owner
accepted PKA-006/012–014 and authorized publication and integration into dev.
