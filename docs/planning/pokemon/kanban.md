# Strixia — Pokémon Agon

Created: 2026-10-12

This is the authoritative status/priority/dependency index. Epic cards define scope and acceptance; the [product brief](../../../products/agon/pokemon/README.md) defines requirements. PKA-004 local Git setup is owner-accepted. The owner accepted PKA-000, PKA-001–003 and PKA-063 and authorized publication/integration on 2026-10-13. Production implementation still requires story approval.

P0 = foundation; P1 = first useful analysis/research; P2 = stronger preparation/practice; P3 = deferred. These priorities describe value, not permission or a promised date. S = small, M = several reviewable steps, L/refine = must split before approval. Dependencies are story IDs, not implementation authorization.

## Ready for Discussion

None.

## Ready for Approval

| ID | Story | Epic | Priority | Size | Dependencies |
| --- | --- | --- | --- | --- | --- |
None.

## In Progress

None.

## In Review

None.

## Done

| ID | Story | Epic | Priority | Size | Dependencies |
| --- | --- | --- | --- | --- | --- |
| [PKA-007](epics/e02.md#pka-007) | Implement a random legal policy | E02 | P0 | S | PKA-006 |
| [PKA-008](epics/e02.md#pka-008) | Execute a full Bo3 set | E02 | P0 | M | PKA-007, PKA-003 |
| [PKA-016](epics/e03.md#pka-016) | Persist one complete baseline set | E03 | P0 | S | PKA-008, PKA-014 |
| [PKA-005](epics/e02.md#pka-005) | Implement a minimal simulator adapter | E02 | P0 | M | PKA-001, PKA-002, PKA-003 |
| [PKA-011](epics/e03.md#pka-011) | Design the first durable workload | E03 | P0 | S | PKA-001, PKA-003 |
| [PKA-006](epics/e02.md#pka-006) | Enumerate legal doubles decisions | E02 | P0 | M | PKA-005 |
| [PKA-012](epics/e03.md#pka-012) | Implement durable run metadata | E03 | P0 | M | PKA-011 |
| [PKA-013](epics/e03.md#pka-013) | Store immutable workload artifacts | E03 | P0 | S | PKA-012 |
| [PKA-014](epics/e03.md#pka-014) | Execute bounded parallel games locally | E03 | P0 | M | PKA-012, PKA-013 |
| [PKA-001](epics/e01.md#pka-001) | Probe Champions simulator compatibility | E01 | P0 | S | None |
| [PKA-002](epics/e01.md#pka-002) | Validate Champions stat allocations and legality | E01 | P0 | S | PKA-001 |
| [PKA-003](epics/e01.md#pka-003) | Define player observations and Bo3 knowledge | E01 | P0 | S | PKA-001, PKA-002 |

- [PKA-000: Deliver the complete planning board](epics/e01.md#pka-000) — E01, P0, M, no dependencies. Owner accepted and authorized integration on 2026-10-13.
- [PKA-063: Apply the Strixia identity](epics/e01.md#pka-063) — E01, P0, S, no dependencies. Owner accepted and authorized integration on 2026-10-13.

- [PKA-004: Establish main/dev/task branch workflow](epics/e01.md#pka-004) — E01, P0, S, no dependencies. Owner accepted the verified local setup on 2026-10-13 and separately configured/published the main/dev remote baseline.

## Blocked

None.

## Backlog

| ID | Story | Epic | Priority | Size | Dependencies |
| --- | --- | --- | --- | --- | --- |
| [PKA-009](epics/e02.md#pka-009) | Restore and branch controlled states | E02 | P1 | M | PKA-005 |
| [PKA-010](epics/e02.md#pka-010) | Build a doubles-aware tactical baseline | E02 | P1 | M | PKA-006, PKA-002, PKA-007 |
| [PKA-015](epics/e03.md#pka-015) | Expose run submission and status | E03 | P1 | S | PKA-014 |
| [PKA-017](epics/e04.md#pka-017) | Parse recorded simulator traces | E04 | P0 | S | PKA-016 |
| [PKA-018](epics/e04.md#pka-018) | Import public Showdown replays | E04 | P1 | M | PKA-017 |
| [PKA-019](epics/e04.md#pka-019) | Create the first real Strixia web route | E04 | P1 | M | PKA-015 |
| [PKA-020](epics/e04.md#pka-020) | Render the Theoria replay viewer | E04 | P0 | M | PKA-017, PKA-019 |
| [PKA-021](epics/e04.md#pka-021) | Import team text and optional stat spreads | E04 | P1 | S | PKA-002 |
| [PKA-022](epics/e04.md#pka-022) | Gate counterfactual analysis by state fidelity | E04 | P1 | S | PKA-009, PKA-018, PKA-021 |
| [PKA-023](epics/e05.md#pka-023) | Represent hidden-state scenario priors | E05 | P1 | M | PKA-003, PKA-021 |
| [PKA-024](epics/e05.md#pka-024) | Update beliefs from observed damage and order | E05 | P1 | M | PKA-023, PKA-002 |
| [PKA-025](epics/e05.md#pka-025) | Carry justified knowledge across the set | E05 | P1 | S | PKA-024, PKA-008 |
| [PKA-026](epics/e05.md#pka-026) | Explain uncertainty and belief changes | E05 | P1 | S | PKA-025, PKA-020 |
| [PKA-027](epics/e06.md#pka-027) | Define a grounded heuristic evaluator | E06 | P1 | S | PKA-010 |
| [PKA-028](epics/e06.md#pka-028) | Estimate outcomes under baseline continuations | E06 | P1 | M | PKA-009, PKA-010, PKA-023 |
| [PKA-029](epics/e06.md#pka-029) | Solve a bounded simultaneous-action matrix | E06 | P1 | M | PKA-006, PKA-009, PKA-027, PKA-023 |
| [PKA-030](epics/e06.md#pka-030) | Evaluate double-oracle action expansion | E06 | P2 | M | PKA-029 |
| [PKA-031](epics/e06.md#pka-031) | Compare search depth and chance allocation | E06 | P2 | L/refine | PKA-029 |
| [PKA-032](epics/e06.md#pka-032) | Validate and calibrate learned evaluation | E06 | P1 | M | PKA-041, PKA-047 |
| [PKA-033](epics/e06.md#pka-033) | Detect decision regret without hindsight | E06 | P1 | M | PKA-029, PKA-026, PKA-022 |
| [PKA-034](epics/e06.md#pka-034) | Render payoff heatmaps and alternative actions | E06 | P1 | S | PKA-029, PKA-020 |
| [PKA-035](epics/e07.md#pka-035) | Curate a versioned M-C team corpus | E07 | P0 | M | PKA-002, PKA-021 |
| [PKA-036](epics/e07.md#pka-036) | Assess replay demonstrations for initialization | E07 | P1 | S | PKA-018, PKA-035, PKA-003 |
| [PKA-037](epics/e07.md#pka-037) | Define the trainable VGC environment | E07 | P0 | M | PKA-006, PKA-008, PKA-003 |
| [PKA-038](epics/e07.md#pka-038) | Compare compact policy/value representations | E07 | P1 | M | PKA-037, PKA-035 |
| [PKA-039](epics/e07.md#pka-039) | Evaluate PufferLib and a transparent PPO reference | E07 | P1 | M | PKA-037, PKA-038 |
| [PKA-040](epics/e07.md#pka-040) | Run a tiny learning correctness experiment | E07 | P1 | S | PKA-039 |
| [PKA-041](epics/e07.md#pka-041) | Train the first M-C policy/value checkpoint | E07 | P1 | M | PKA-040, PKA-035, PKA-038 |
| [PKA-042](epics/e07.md#pka-042) | Compare direct RL with replay initialization | E07 | P2 | M | PKA-041, PKA-036 |
| [PKA-043](epics/e07.md#pka-043) | Compare historical opponent sampling | E07 | P1 | M | PKA-041, PKA-047 |
| [PKA-044](epics/e07.md#pka-044) | Test a reusable Champions base checkpoint | E07 | P2 | L/refine | PKA-041, PKA-043, PKA-035 |
| [PKA-045](epics/e07.md#pka-045) | Profile and optimize the measured training bottleneck | E07 | P1 | M | PKA-041, PKA-039 |
| [PKA-046](epics/e08.md#pka-046) | Record experiment and model lineage | E08 | P1 | S | PKA-013, PKA-040 |
| [PKA-047](epics/e08.md#pka-047) | Build the offline model league | E08 | P1 | M | PKA-016, PKA-010, PKA-035 |
| [PKA-048](epics/e08.md#pka-048) | Gate champion promotion by evidence | E08 | P1 | S | PKA-046, PKA-047, PKA-041 |
| [PKA-049](epics/e08.md#pka-049) | Show actual experiments in Strixia Lyceum | E08 | P1 | M | PKA-046, PKA-047, PKA-019 |
| [PKA-050](epics/e09.md#pka-050) | Evaluate preview candidate selections | E09 | P1 | M | PKA-021, PKA-029, PKA-047 |
| [PKA-051](epics/e09.md#pka-051) | Run a matchup Gauntlet | E09 | P1 | M | PKA-047, PKA-050, PKA-035 |
| [PKA-052](epics/e09.md#pka-052) | Expand interactive scenario branches on demand | E09 | P2 | M | PKA-009, PKA-023, PKA-029, PKA-034, PKA-019 |
| [PKA-053](epics/e10.md#pka-053) | Play a local turn-by-turn practice battle | E10 | P2 | M | PKA-008, PKA-019, PKA-021 |
| [PKA-054](epics/e10.md#pka-054) | Add coaching and consensual local scrims | E10 | P2 | M | PKA-053, PKA-026, PKA-029 |
| [PKA-055](epics/e11.md#pka-055) | Specify stat-spread optimization objectives | E11 | P2 | S | PKA-002, PKA-051 |
| [PKA-056](epics/e11.md#pka-056) | Implement a breakpoint-based spread optimizer | E11 | P2 | M | PKA-055, PKA-024 |
| [PKA-057](epics/e11.md#pka-057) | Evaluate spread candidates through matchup evidence | E11 | P2 | M | PKA-056, PKA-051 |
| [PKA-058](epics/e11.md#pka-058) | Explore team-planner candidates | E11 | P3 | L/refine | PKA-057, PKA-051 |
| [PKA-059](epics/e12.md#pka-059) | Prepare a secure public pilot | E12 | P2 | L/refine | PKA-020, PKA-015, PKA-014 |
| [PKA-060](epics/e12.md#pka-060) | Deploy an explicitly approved release | E12 | P3 | M | PKA-059 |
| [PKA-061](epics/e12.md#pka-061) | Explore decision puzzles and spectator mode | E12 | P3 | L/refine | PKA-033, PKA-048, PKA-052 |
| [PKA-062](epics/e12.md#pka-062) | Assess future Champions formats and public bots | E12 | P3 | L/refine | PKA-048, PKA-060 |
| [PKA-064](epics/e09.md#pka-064) | Review VGC Planner workflows | E09 | P2 | S | None |
| [PKA-065](epics/e03.md#pka-065) | Assess mid-turn recovery | E03 | P2 | S | PKA-009, PKA-014 |
| [PKA-066](epics/e03.md#pka-066) | Assess shared execution and cloud failover | E03 | P2 | S | PKA-013, PKA-014 |
| [PKA-067](epics/e01.md#pka-067) | Run milestone Ponytail audits | E01 | P1 | S | None |

## Change history

- 2026-10-14: Owner accepted PKA-007/008/016 and authorized committing, pushing
  and merging all accumulated work into dev; moved the three cards to Done. Added
  PKA-067 for milestone audit cadence; future stories remain unapproved backlog.

- 2026-10-14: PKA-007/008/016 implemented, verified and moved to In Review. Agon 0.5.0
  adds the random paired policy/scoring; the existing worker records and resumes
  parallel independent sets. Independent review found a consecutive bilateral-request
  rollback defect, now fixed and covered by a real-engine regression. Owner acceptance
  and publication remain pending.

- 2026-10-14: Owner approved implementation of PKA-007/008/016 after selecting
  uniform complete paired-action sampling and pinned Showdown Bo3 scoring. The
  batch retains observed public history without inference, uses completed-game
  recovery and reuses the local coordinator for parallel independent sets. No
  trainer, API, website, cloud service, push or merge is included.

- 2026-10-14: Owner explicitly accepted PKA-005's Python simulator adapter and
  PKA-011's durable-workload design after the completed audit; moved both to Done.
  This acceptance does not authorize new feature implementation or publication.

- 2026-10-14: PM review corrected stale foundation/integration guidance and action
  coverage, selected PKA-007/008/016 for discussion only, added PKA-007 as the random
  comparison prerequisite for PKA-010, and removed the public-replay prerequisite
  from PKA-027's controlled-state evaluator. Imported-replay analysis still requires
  PKA-022. Renamed PKA-014 to reflect its implemented bounded parallel games.
  No new implementation, publication or spending is authorized by this refresh.
  Coherence, feasibility and scope reviews completed. Validation passed: 67 unique
  cards/board entries, dependency references/cycle checks, local links/anchors and
  instruction paths, locked sync, Ruff lint/format, mypy and 49 repository tests.

- 2026-10-13: Owner accepted completed planning, branding and foundation work and authorized commit/push/merge. Moved PKA-000, PKA-001–003 and PKA-063 to Done; selected PKA-005 and PKA-011 for discussion only. Training remains Python; Node is limited to the simulator boundary.

- 2026-10-13: PKA-003 verified and moved to In Review; all three guided foundation cards await owner acceptance. Research reports document client stat/validator gaps and official evidence limits. No production implementation or publication.

- 2026-10-13: PKA-002 verified and moved to In Review. Fractional validator gap and official evidence gaps recorded; dependent PKA-003 may continue under guided-batch approval.

- 2026-10-13: PKA-001 verified and moved to In Review. Owner approved continuing dependent PKA-002–003 from verified findings without automatic acceptance.

- 2026-10-13: Owner accepted PKA-004 and approved PKA-063's full local Strixia migration. Renamed current branding without changing existing task IDs, priorities or dependencies. Added PKA-064 as a Backlog workflow review with no prerequisite; listing VGC Planner does not authorize implementation.

- 2026-10-12: Created the full-scope board from the owner-approved product direction. Statuses are planning states only. Story implementation and acceptance require separate owner decisions.

- 2026-10-12: PKA-000 moved to In Review after documentation and scaffold checks; owner acceptance pending.

- 2026-10-13: Recorded atomic commit/version policy and a shorter planning entry point. PKA-004 initial snapshot/dev setup moved to Ready for Approval; no commit, tag or branch created.

- 2026-10-13: Owner approved PKA-004. Saved the reviewed 67-file baseline, created dev from main, verified checks and moved PKA-004 to In Review. Setup evidence is a separate small initialization commit; branch heads are aligned. Future tasks use task branches and reviewed merge requests into dev when a remote is authorized.

- 2026-10-13: PKA-063 moved to In Review after root checks, package builds, independent wheel imports, local link/instruction validation and task metadata/dependency checks. PKA-064 remains Backlog; PKA-001–003 have not started.

- 2026-10-13: Owner approved implementation and publication of PKA-005 and the PKA-011 design. Delivered cards remain In Review pending final owner acceptance; merge authorization does not imply a review of the resulting source.

- 2026-10-13: Owner approved and locally implemented PKA-006 and PKA-012–014 together; moved verified cards to In Review. Added PKA-065/066 for future resilience and a regulation revalidation gate under PKA-062. No automatic acceptance, push, merge or cloud spend.

- 2026-10-13: Owner accepted tested PKA-006 and PKA-012–014 and explicitly authorized push and merge into dev; moved those four cards to Done. Future-regulation, search and resilience stories remain unimplemented backlog.
