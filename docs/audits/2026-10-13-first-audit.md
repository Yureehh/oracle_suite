# First repository audit — 2026-10-13

**What this repo does:** Strixia currently runs local Champions M-C doubles games
from Python against a pinned Node simulator. It supplies player-visible paired
choices and saves independent game results in SQLite and checked files. This audit
assumes one local operator on macOS/Linux, with bounded parallel games; it does not
assume a public service or a high-throughput RL trainer.

The owner invoked Ponytail Audit and explicitly authorized fixes, overriding its
usual report-only scope. The audit traced native team inputs, simulator transport,
player projections, paired choices, rejected-choice rollback, batch admission,
publication, cancellation/resume, exports and backups. It also inspected dependency
and build configuration, CI, hooks, research probes and behavior tests.

## Must fix — fixed locally

1. **A backup can replace another writer's file**
   ([source](../../packages/python/strixia_core/src/strixia_core/runs.py)).
   - **What this is:** Core copies run metadata into a new SQLite backup.
   - **Problem:** Another writer can create the destination after the existence check.
     SQLite then opens that file and replaces its contents.
   - **Fix:** Reserve the filename using exclusive creation. The regression simulates
     a stale existence check and verifies that the competing database stays unchanged.
   - **If we skip it:** Concurrent backups can destroy the earlier backup.

2. **Closing the progress reader changes experiment results**
   ([source](../../apps/worker/local.py)).
   - **What this is:** The worker prints progress after saving each completed game.
   - **Problem:** A closed pipe raises BrokenPipeError inside game error handling,
     marks the run failed and stops admitting the remaining games.
   - **Fix:** Handle progress separately from execution/publication and ignore a closed
     progress pipe. The regression verifies both games remain saved and successful.
   - **If we skip it:** Output consumers can cause false failures and unfinished batches.

3. **Finishing on the final allowed decision is rejected**
   ([worker](../../apps/worker/local.py), [demo](../../scripts/pokemon_battle.py)).
   - **What this is:** Both entrypoints cap decision boundaries to prevent endless games.
   - **Problem:** They checked completion only before an action, so ending on the final
     permitted action still raised the limit error.
   - **Fix:** Check completion after the bounded loop. A controlled simulator verifies
     the exact boundary in both entrypoints and rejection beyond the worker boundary.
   - **If we skip it:** Valid completed games at the limit are discarded as failures.

## Should fix — fixed locally

4. **Runtime and test documentation still describes the scaffold**
   ([deployment](../architecture/deployment.md), [testing](../conventions/testing.md)).
   - **What this is:** These docs explain prerequisites and what checks establish.
   - **Problem:** They said development needed only Python/uv, had no database, and
     tests did not check simulator behavior; Node, SQLite and engine tests now exist.
   - **Fix:** Describe current local behavior and distinguish future hosting and actual
     game fidelity. Add the reproduced lessons to [Python standards](../conventions/python.md)
     and link those standards from the root instructions.
   - **If we skip it:** New contributors follow incomplete setup and misunderstand evidence.

## Verification and delivery

The three new regressions failed against the original implementation, then passed
after the fixes. Final checks passed:

- Locked workspace sync; Ruff lint and format; strict mypy (17 files).
- All 49 root tests and all 15 standalone foundation tests, with no skips. These
  include real engine batches, action edge cases, rollback, information boundaries,
  snapshot continuation, claim contention and interrupted-run recovery.
- Standalone foundation mypy (2 files); all ten pre-commit hooks.
- Core 0.3.1 source/wheel build and isolated wheel import/version verification.
- Local Markdown links, anchors and instruction paths; Git whitespace checks.

Core alone moves to 0.3.1 for the compatible backup fix. Root and Agon versions,
dependencies, task acceptance and simulation scope stay unchanged. Implementation
commits are `3b19dbd` (backup) and `b358589` (worker/demo). Changes are local on
`codex/first-repo-audit`, based on the unpushed tooling branch.

**Verdict:** The current local architecture is proportionate to its workload after
these fixes. Snapshot rollback and artifact publication checks serve real guarantees;
removing them to reduce line count would weaken correctness. No concrete dependency
removal or broad refactor was justified. No new runtime dependencies were added.

**Not checked:** Training-scale performance, GPU behavior, multi-host/cloud operation,
Windows, the external Bets project, exhaustive upstream simulator correctness or
dependency advisories. The poke-env server experiment was inspected but not rerun.
GitHub CI was not dispatched. Revision/lock checks are not verification against an
operator modifying local generated engine files. A closed CLI output reader may still
make the final CLI print fail; it no longer changes saved batch status. Backup failure
can leave an incomplete destination that must be removed before retrying.
