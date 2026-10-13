# PKA-011: First durable workload

Design delivered 2026-10-13; implementation and publication authorized by the owner.
The original PKA-011 design is retained as a reference below. PKA-005 provides
one controlled Python game; PKA-012–014 now implements the local subset described
in the delivery section. PKA-008 and PKA-016 will connect complete Bo3 execution and storage.

## Implemented local delivery — 2026-10-13

Owner requested PKA-012–014 as one batch, accepted local SQLite and a small batch of
independent seeded games, and asked to limit recovery effort while preserving the
future parallel RL workload. The full design below remains a reference; not every
future coordination mechanism belongs in the first local delivery.

Delivered minimum: retain committed per-game results and immutable artifacts, provide
explicit resume of unfinished games, and report failures clearly. Mid-turn restoration,
cloud failover and distributed lease/heartbeat infrastructure are outside the
first scope. Minimal integrity checks and protection against duplicate publication
remain necessary. Worker ownership uses an exclusive local OS lock; restart is an explicit resume.

The execution coordinator is distinct from parallel battle environments. Database
writes belong at workload/result boundaries, not every simulated turn. Bounded parallel
independent games are implemented; they require per-game completion identity
because results may finish out of order. Resume unfinished game IDs rather than only
a consecutive prefix. Games within one future Bo3 stay ordered when knowledge from
one game affects the next. RL training checkpoints are separate from game-run recovery.

The [batch runbook](../../runbooks/local-batches.md) documents the delivered scope.
Failed/cancelled runs can be explicitly resumed under the exclusive local lock;
succeeded runs remain terminal. This supersedes the earlier design's new-run-only
terminal retry proposal. Distributed leases/heartbeats, shared storage and mid-turn
snapshots below are future reference design, tracked by PKA-065/066, not implemented.

## Original design and future extension reference

The remaining sections describe the broader design, including future Bo3 and
distributed coordination. The implemented subset and superseding retry decisions
are stated above; these sections are not a claim of additional runtime support.

## Workload and recovery boundary

The first durable job is a bounded local Champions M-C match run. Begin with one
seeded game using the [Python adapter](foundation/005-adapter.md). Extend to Bo3
only after its set rules and legal policies exist. No generic queue framework,
trainer, distributed scheduler or API is required to prove local recovery.

**Resume after the last durably completed game.** If game two is interrupted,
retain game one's result and knowledge; replay game two from its start. Do not try
to serialize a live Node process or resume mid-turn. An engine result is completed
computation, but it becomes a durable completed game only after the publication
transaction commits. A crash between those events may repeat computation.

A completed-game boundary includes its result, trace manifest, next-game seed,
score and permitted chronological set-knowledge ledger. Future stateful policies
must also save their version and game-boundary RNG/state needed to replay the next
game. Missing required state makes recovery unsupported and explicitly failed;
never silently substitute a newer policy or model. PKA-005 does not yet implement
this ledger or policy state. Training checkpoints are a separate future workload.

Transient HP, field effects and selections reset between games. Revealed facts and
inferred ranges remain separate in the ledger, as specified in
[PKA-003](foundation/003-observations.md). Incomplete-game evidence must not enter
permitted set knowledge. Saved game-one observations cannot be modified by later
revelations. Full private traces belong to trusted research storage, not policy views.

## Frozen identity and provenance

Before a run becomes queued, validate and freeze a versioned configuration:

| Field | Purpose |
| --- | --- |
| `run_id`, submission key, configuration digest | Stable identity and duplicate submission handling |
| Schema version and workload type | Reject incompatible or unknown future inputs |
| Format ID and game/set stopping rules | Preserve M-C scope and bounded execution |
| Two native teams and their digest | Exact point allocations, moves, items, abilities and natures |
| Engine revision and npm lock digest | Reproduce mechanics and dependency build |
| Python package version, code revision, Python/Node versions | Reproduce the adapter/runtime |
| Game seed schedule and policy seeds | Separate engine chance from policy randomness |
| Policy/model identifier and immutable digest, if used | Reject missing or changed policy artifacts |
| Maximum games, decision limit and deadline | Bound cost and abnormal execution |

Use canonical JSON with sorted keys, explicit integer point values and a recorded
canonicalization version, then SHA-256 for identity. Hashes detect change; they do
not establish authenticity. Retain the actual configuration, not just its digest.
The initial demo's engine-default policy must be identified as such, never relabeled
as the future random or tactical policy.

Submitting the same key and digest returns the original run ID and status. Reusing
a key with different inputs is a conflict. An intentional repeat uses a new key.
Finished games are numbered consecutively; `(run_id, game_index)` is unique. Recovery
checks provenance and hashes before executing; version mismatch stops for review.

## States, attempts and claims

| State | Allowed next state | Meaning |
| --- | --- | --- |
| queued | running, cancelled | Frozen input awaiting a claim |
| running | succeeded, failed, cancelled, queued | Active attempt; expired claim may requeue |
| succeeded | none | All required game boundaries published and stop rule satisfied |
| failed | none | Explicit unrecoverable input, protocol or execution failure |
| cancelled | none | Cancellation acknowledged; previous completed games retained |

Every transition records time, attempt identity and reason. Terminal retries are new
runs referencing the old run; lease recovery is a new attempt on the same run.
Cancellation is a request flag until acknowledged, not premature terminal success.
A completed terminal result wins a subsequent cancellation race; cancellation does
not erase it. A durable cancellation request blocks new claims.

A claim transaction changes queued to running, increments a monotonically increasing
attempt/fencing number and records worker ID, heartbeat and expiry. Heartbeats and
publication compare the current attempt number. This prevents an old worker that
wakes up after its claim expired from committing results. One local worker is the
initial scope, but a two-worker race must still produce one current claim.

A heartbeat expiry makes the attempt recoverable; it is not proof its process died.
Requeue atomically against the expired attempt, then start from the last published
game. Stop an old local child where possible; fencing protects metadata even if it
continues computing. Lease durations and heartbeat cadence are implementation
parameters to measure in PKA-014, not guessed performance requirements here.

For graceful cancellation, finish and publish an already-running bounded game, then
acknowledge cancellation before starting another. A forced stop discards that
unfinished game's durable progress and retains previous games. On recovery, a
pending cancellation is acknowledged without starting a new game. Irrecoverable
errors retain completed evidence plus an explicit error record; do not report success
because a subprocess exited normally.

## Metadata and artifact candidates

The existing architecture names PostgreSQL as a candidate, not an installed choice.
The smallest local implementation should compare these options before PKA-012:

| Candidate | Fit | Limit |
| --- | --- | --- |
| SQLite metadata + local files | Embedded single-machine transactions; little setup | One writer; shared multi-host storage is outside this choice |
| PostgreSQL metadata + local files | Concurrent transactional claims and future shared services | A server adds setup/operation for the first local job |
| JSON metadata + local files | Easy inspection | Claims, migrations and multi-record publication require custom transaction logic |

SQLite is a reasonable local-first recommendation, subject to the PKA-012 discussion;
this design does **not** select or install it. Its documented deployment guidance
favors local embedded storage and distinguishes workloads needing client/server
concurrency. [SQLite deployment guidance](https://www.sqlite.org/whentouse.html).
PostgreSQL provides explicit row locking for transactional coordination.
[PostgreSQL locking documentation](https://www.postgresql.org/docs/current/explicit-locking.html).
Avoid inventing a transactional JSON database. Whichever metadata backend is chosen,
keep large traces and future checkpoints as files with integrity metadata.

Local artifacts live under an ignored runtime directory, with run/attempt/game
identity. Record relative paths under that root, digest, byte count, media type and
schema version in the manifest. Reject paths escaping the storage root. Private
traces need explicit access boundaries before any public API is introduced.

## Publication and crash safety

Filesystem and metadata do not share a transaction. Publish in this order:

1. Write immutable, attempt-specific staged artifacts on the target filesystem.
   Flush file data, verify digest/size and close the files.
2. Rename into unique final paths on the same filesystem, ensuring durable directory
   entries where the selected platform supports it. Never replace another attempt's
   files. Failures remain visible; filesystem durability must be tested on the actual
   supported platform during PKA-013.
3. In one metadata transaction, verify the current claim, insert the unique completed
   game and artifact manifest, advance score/knowledge/progress, and optionally mark
   the run succeeded. Only this commit publishes the game to readers.

If step three fails, files may be orphaned, but readers see no completed game.
Recovery can recompute the game. Garbage collection must ignore active attempts and
retain committed artifacts; no cleanup worker is needed for the first slice.
A committed manifest with missing/corrupt files is an integrity failure, not a
completed result to return silently. Preserve the record for diagnosis and fail
recovery explicitly. Do not promise exactly-once computation: uniqueness and fencing
provide one accepted publication, even when computation is repeated.

Terminal publication is idempotent for the same current attempt and identical game
manifest. A different digest for an already published game is a conflict. A stale
attempt cannot overwrite progress or change a terminal state.

## Migrations and inspection

Version metadata schemas, manifests and configuration separately. Reject unsupported
newer schemas rather than guessing. PKA-012 must include a backup/export and a
migration test preserving run IDs, configuration digests, transitions and artifact
references. Verify referential integrity and hashes after migration before promotion.
Keep migrations scoped to the selected backend; no ORM or generic persistence layer
is required by this design.

Provide a local inspection path for run status, attempt/recovery reason, last completed
game and artifact integrity. Full persisted seeds/private traces are trusted operator
information. API submission and user-visible status remain PKA-015.

## Acceptance examples for downstream tests

| Scenario | Required observable result | Owner story |
| --- | --- | --- |
| Same submission repeated; same key with changed team | Same run ID; changed input rejected | PKA-012 |
| Two workers race to claim | Exactly one current attempt | PKA-014 |
| Worker dies during game two | Game one retained; game two reruns from fixed inputs | PKA-014/016 |
| Engine finishes; process dies before metadata commit | No visible completed game; safe recomputation | PKA-013/014 |
| Partial artifact write or failure after rename | No manifest published; staged/orphan file observable | PKA-013 |
| Expired worker returns after another attempt starts | Old heartbeat/result rejected by fencing | PKA-014 |
| Completion submitted twice | Identical publication is idempotent; changed digest rejected | PKA-012/013 |
| Graceful cancel or forced interruption | Retain committed games; no new game after acknowledgement | PKA-014/016 |
| Result commit races cancellation | Transaction order decides terminal state; never both | PKA-012/014 |
| Missing artifact, changed model, unsupported schema | Explicit integrity/version failure before execution | PKA-012/013 |
| Game-three knowledge is richer | Saved game-one player observations unchanged | PKA-016 |
| Backup migrated and restarted | IDs/progress/hashes survive; restart selects next game | PKA-012/016 |

Design review checked these scenarios against PKA-005's single-game process boundary
and PKA-003's visibility rules. None of these persistence fault tests has run yet;
they are acceptance requirements for the implementation stories. This document
adds no database dependency, storage adapter, worker, API or performance claim.
