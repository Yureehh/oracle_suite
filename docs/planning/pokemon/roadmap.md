# Dependency-aware roadmap

Created: 2026-10-12

The [board](kanban.md) owns task ordering dependencies and state. This roadmap groups
outcomes; it does not authorize implementation or promise deadlines. The complete
end-to-end scope is Train → Evaluate → Analyze → Prepare → Simulate → Practice → Improve.

| Stage | Deliverable and value | Main story group | Main risk | Exit evidence |
| --- | --- | --- | --- | --- |
| 0 | Trustworthy Champions M-C integration choices | PKA-001–004 | Client/engine/stat mismatch | Pinned compatibility report, rule examples, player/set information contract |
| 1 | Legal baseline battles and durable recorded sets | PKA-005–017 | Invalid actions, process failure, leakage | Complete repeatable Bo3, artifacts and restart/failure checks |
| 2 | First useful Theoria web viewer | PKA-018–022 | Replay incompleteness | Real turn navigation with explicit unknowns and analysis eligibility |
| 3 | Belief-aware tactical analysis | PKA-023–029, 034 | Unsupported counterfactual certainty | Grounded facts/scenarios and bounded candidate matrix with visible assumptions |
| 4 | Trainable Champions model and real research visibility | PKA-035–043, 046–049 | Throughput/generalization | Bounded actual training, grouped held-out league, lineage and honest Lyceum views |
| 5 | Stronger decision analysis and tournament preparation | PKA-030–033, 050–052 | Search cost and pilot-dependent team ratings | Equal-budget experiments, calibrated support, regret evidence, preview and Gauntlet |
| 6 | Reusable base, practice and optimization | PKA-044–045, 053–058 | Negative transfer and surrogate-objective bias | Transfer comparisons, local play, feasible spread tradeoffs and matchup evidence |
| 7 | Approved public release and optional extensions | PKA-059–062 | Privacy, workload cost and scope expansion | Reviewed staging, authorization, backup/rollback, approved deployment |

Order is not a single serial chain: import/viewer work can proceed once its facts are
available; training can progress beside analysis. Search remains optional and no
strong RL agent is a prerequisite for replay viewing. Local baseline practice can
arrive before a champion. A promoted checkpoint can be offered later without making
training a dependency of the first practice interface. Team parsing/corpus preparation
can proceed without the viewer, so model research is not blocked by frontend delivery.

## Current sequencing

The owner accepted [foundation research](foundation/README.md), paired choices and
local durable independent-game batches. The owner explicitly accepted the adapter
and durable-workload design on 2026-10-14. The [board](kanban.md) remains authoritative;
implementation, acceptance and publication are separate decisions.

The following connected slice is implemented and owner-accepted:

1. [PKA-007](epics/e02.md#pka-007): a seeded Python policy sampling complete paired
   choices. Engine-default choices in the existing scripts are not this baseline.
2. [PKA-008](epics/e02.md#pka-008): ordered Bo3 games with fixed teams, fresh previews,
   correct resets and chronological permitted evidence.
3. [PKA-016](epics/e03.md#pka-016): save that set using the existing run/artifact
   storage, retaining completed-game progress without mid-turn recovery.

The owner selected uniform paired sampling and pinned Showdown series scoring, then
approved implementation on 2026-10-14. Games within a set are sequential; independent
sets run in parallel. This slice adds no API, website, trainer, paid compute or new
persistence framework. The owner accepted all three and authorized integration into dev on 2026-10-14.

Next branches of work are [PKA-010](epics/e02.md#pka-010), a tactical baseline after
the random policy, and [PKA-021](epics/e04.md#pka-021), native team input before
[PKA-035](epics/e07.md#pka-035), the training/evaluation corpus. Then
[PKA-037](epics/e07.md#pka-037) specifies the learning environment. Trace parsing and
the viewer remain a separate useful track; they do not gate the training environment.

## End of 2026

The owner has not fixed weekly time, hardware or paid budget. Model/data design comes
first; throughput and pilot experiments then determine required compute. Do not infer
availability from permission to leave a PC running all day. No spending is authorized.

Provisional target: stages 0–2, then a narrow evidence-based analysis slice. First PPO
and basic League/Lyceum are stretch outcomes until measured. Strong generalization,
advanced search, complete Techne and public hosting are longer-term work. Reassess the
calendar after simulator compatibility, corpus availability and actual learning pilots.
Frozen M-C remains a reproducible reference even when the live regulation changes.
Support a later Champions regulation only through an explicit compatibility/adaptation
story; do not silently relabel old models as current.

## Decision gates

Simulator/client selection: PKA-001. Champions allocations: PKA-002. Observation/action
contract: PKA-003/006/037. Model/data: PKA-035–038. PufferLib/trainer: PKA-039.
Compute budget: after model/data choices and measured pilots, before scaling PKA-041.
Search breadth/depth: PKA-029–031. Champion: PKA-048. Public release: PKA-059–060.
Every gate includes an explanation for the owner and an explicit task approval.
