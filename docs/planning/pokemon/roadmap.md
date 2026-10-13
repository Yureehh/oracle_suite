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

## First task

PKA-001 is the recommended first implementation/research task. It is not approved yet.
Its design should constrain versions, legal example teams, local processes, reproducible
probe checks and maximum execution duration. No paid experiment is included. PKA-002
is the closely related stat/legality study; do not absorb it without agreeing scope.

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
