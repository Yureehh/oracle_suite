# Research choices and evidence

Created: 2026-10-12

This is a decision record for planning, not a claim that experiments were run.
Technical candidates require compatibility tests and measured quality/cost comparisons.

## Champions rules and integration

Current scope is Champions Regulation M-C (owner's “Reg C”), doubles Bo3 OTS only.
Showdown currently defines `gen9championsvgc2026regmc` and its Bo3 variant using a
Champions mod, not ordinary Scarlet/Violet mechanics. Study Champions stat allocations,
legality, rounding, PP and mechanics; do not create historical EV/IV training support.
The inspected Champions validator requires maxed IVs, while native stat points occupy
the engine's `evs` field. The normal fixed-level implementation computes HP as base
HP + allocated points + 75, and other stats as base + points + 20 before nature rounding.
Field naming is not permission to apply the old 252-EV formula. Numeric allocation caps
and complete format legality must be verified in PKA-002 before contracts/code.

Sources: [format definitions](https://github.com/smogon/pokemon-showdown/blob/master/config/formats.ts),
[Champions stat calculation](https://github.com/smogon/pokemon-showdown/blob/master/data/mods/champions/scripts.ts),
[validator](https://github.com/smogon/pokemon-showdown/blob/master/sim/team-validator.ts),
[Champions rules](https://github.com/smogon/pokemon-showdown/blob/master/data/mods/champions/rulesets.ts).
Showdown is a community simulator, so pinned source checks do not prove console parity.
Record primary rule evidence and any unresolved mechanics disagreements.

Use Showdown as the starting reference with poke-env for player orchestration where
validated, and a narrow Node simulator bridge for controlled branching. Do not claim
these are universally the best packages. Compare documented APIs, correctness, state
access, development burden and measured performance in PKA-001. The inspected poke-env
`GenData.from_format` selects data by generation, creating an unverified Champions-mod
compatibility risk. Use actual engine requests/data for legality; patch or replace only
an inadequate integration layer if evidence warrants it. A custom battle engine is a
separate high-cost decision requiring benchmarks, parity tests and owner approval.

Sources: [poke-env data loader](https://github.com/hsahovic/poke-env/blob/master/src/poke_env/data/gen_data.py),
[Showdown simulator API](https://github.com/smogon/pokemon-showdown/blob/master/sim/SIMULATOR.md).
Inspection references from 2026-10-12: Showdown `942cda71d14bf0618bd57991708a2e2734b6daba`,
poke-env `7ff6212e4e738efd46f1ea52035b37a8bba1e386`. No dependency is installed/pinned in
Strixia yet; PKA-001 must recheck and select an exact tested pair.

## PufferLib: conditional candidate

The current official 5.0 docs describe native C/CUDA environments and training, with
CPU evaluation but no CPU training. Older 3.0 source uses Python/PyTorch. These are
different integration targets; generic older wrapper examples do not establish 5.0
compatibility. Advertised performance is not a VGC benchmark.

[Official docs](https://puffer.ai/docs.html),
[3.0 trainer source](https://github.com/PufferAI/PufferLib/blob/3.0/pufferlib/pufferl.py).
Inspected branch revisions: 5.0 `6ffa5b10dbbbe4d1e8288367c7d9d3acd3bad4a2`,
3.0 `3b5c6046bb8b46685d62d151720025507e3418c2`; neither is adopted.

PKA-039 compares compatibility and end-to-end learning cost against a transparent
PyTorch/CleanRL-style reference. Check custom coordinated actions/masks, recurrence,
terminal/truncation/reset behavior, opponent checkpoint sampling, CPU smoke paths,
model export and interrupted-run recovery. Profile simulator/Node IPC, collection,
inference and gradient updates separately. A faster trainer does not fix a simulation
bottleneck or incorrect transitions. Native integration cost may exceed its benefit.
Adopt only if correctness and measured quality per time/cost improve. Do not introduce
PufferLib's visualization as a second authoritative experiment store alongside Lyceum.

Alternative reference: [CleanRL PPO implementations](https://docs.cleanrl.dev/rl-algorithms/ppo/).
Neither library is installed, benchmarked or demonstrated working with Strixia today.
No claim of a universally best RL library is justified.

## Model, data and regulation transfer

Confirmed: train only Champions; no Random Battles prerequisite; quality and learning
are goals. Recommended: curated diverse M-C tournament teams with grouped held-out
compositions/sources; tag unknown or imputed spreads, never present them as truth.
Replay BC data must contain recoverable observations/actions without hidden-state or
chronological leakage. Raw replay availability does not imply complete training labels.

Hypothesis: a compact policy/value encoder with coordinated masked actions and explicit
history or recurrence can form a strong base. Compare MLP/entity encoder and small
attention on measured learning/latency/memory before choosing. PPO is the initial
candidate algorithm, not an approved implementation. Compare direct self-play with
BC-initialized PPO and a simple historical checkpoint mix. Model/data decisions precede
hardware spend; measured pilot costs precede large training. No giant model or cheapest
possible model is prescribed. Select a quality/cost Pareto point with the owner.

A reusable Champions base checkpoint is desirable but not automatically transferable.
First learn M-C competence; for each future regulation validate data/action changes,
compare warm-start against fresh training at equal budget and evaluate negative transfer.
Keep the base immutable; regulation champions are separate versioned descendants.
No usable third-party competitive checkpoint is assumed available. An adaptable
handcrafted tactical baseline remains useful even before our learned base exists.

Research sources, all author-reported unless reproduced here:

- [Nessie](https://www.smogon.com/forums/threads/nessie123-an-ots-vgc-bot-that-topped-the-reg-m-c-bo3-ladder.3789213/): compact evaluator, search-guided play, double-oracle and selective deepening; training makes hidden information unusually public.
- [mikumiku37](https://www.smogon.com/forums/threads/mikumiku37-a-self-play-vgc-bot-reached-1-on-the-vgc-reg-m-c-ladder.3789199/): VGC PPO and historical policies with one-turn candidate matrix search; custom simulator/weights not assumed obtainable and Bo1 results are not our Bo3 validation.
- [Jaxcalibur](https://jaxcalibur.github.io/): policy-only PPO training with custom JAX simulation; Random Singles methods are ideas rather than a VGC pretraining requirement.
- [VGC-Bench](https://arxiv.org/abs/2506.10326): useful team-generalization and evaluation methodology; older benchmark formats/checkpoints need Champions compatibility checks.
- [PokaiTrainer v2](https://arxiv.org/html/2608.29197v2): Champions M-B OTS Bayesian matrix/CFR search and simulation validation; full recipe is deferred.

## Websites and bots for inspiration

The bot/research references above remain model-method inspiration, not adopted engines
or proven Strixia results. Product workflow references belong here alongside them.

### VGC Gameplan Planner

- Website: [VGC Planner](https://vgcplanner.app/).
- Source and author documentation: [phc4rdoso/vgc-planner](https://github.com/phc4rdoso/vgc-planner).
- Inspection date: 2026-10-13. Observed homepage: Regulation M-C label, team folders
  containing opponent gameplans, a Showdown-paste import description, JSON import/export controls,
  and a description of flowchart preparation. Deeper workflows were not exercised.
- Author-documented behavior: branching turn-by-turn gameplans, named/colored lines,
  replay-derived branches and sharing. The README describes turn results using a
  Smogon damage calculator; these are author claims, not reproduced parity tests.
- Primary fit: Delphi's matchup preparation and on-demand branches, especially
  [PKA-050–052](epics/e09.md#pka-050). Metis may later supply agent suggestions for
  those plans; Techne may use the same preparation context for candidate teams and
  spreads. This does not move planning into a separate Metis implementation.
- Documented assumptions: unless explicitly supplied, chance outcomes do not roll;
  moves hit without critical hits, default speed ties favor the listed action order,
  and HP uses average damage rolls. The author notes that Champions changes unknown
  to the calculator are not modeled. These are planner conventions, not Strixia rules.
  Its handling of legacy EV imports is not a requirement for our Champions-only scope.
- Proposed adaptation: study the team/opponent organization, branch navigation and
  presentation of assumptions. Preserve Strixia's authoritative simulator, uncertainty
  and state-fidelity gates; do not claim a replay branch is an exact counterfactual.
- Follow-up: [PKA-064](epics/e09.md#pka-064) produces a bounded workflow review before
  any UI, importer, compatibility layer or mechanics are implemented from this reference.

## Search experiments and evaluation meaning

Start from a correct small matrix game and bounded candidate choices. Double-oracle
adds approximate best-response actions to that restricted matrix; it does not imply
extra future turns. More depth adds future decision states. More chance/world samples
improves estimates under the current model, not model correctness. Benchmark each axis
independently and at equal decision budgets. CFR/regret variants, deep pUCT and selective
expansion need their own evidence; no single algorithm is established as best.

Distinguish heuristic score, expected value versus an opponent model, worst-case value,
restricted-game equilibrium and calibrated continuation win probability. A battle-win
value is not a Bo3 set-win value. A mixed equilibrium can justify several actions; one
bad realized outcome does not prove a blunder. Judge alternatives with pre-decision
beliefs and explicitly declared opponent assumptions. Calibrate only with held-out
outcomes from the specified continuation setting and identify unsupported states.

## Hidden information and replay fidelity

Neutral sampling means a documented distribution over legal scenarios, not random
invalid stats. Learned or metagame priors are optional expectations, never facts.
Update from reveals and damage/order evidence using uncertainty about crits, rolls,
modifiers and rounded HP. A single observed hit rarely identifies an exact spread or
RNG roll. Preserve a timestamped ledger across games, resetting transient battle state.
Policies see observations only; both sides' simulated strategies must respect what
they could know. Otherwise per-world optimization creates strategy fusion/leakage.

The owner chose viewer-only replay behavior when spreads are missing. Supplied spreads
can unlock more grounded facts; even both complete teams do not guarantee exact
counterfactual reconstruction of a public replay. Gate branching on state fidelity,
mark hypothetical states explicitly, and never claim recovered hidden RNG.
Explanations should say, for example, “Game 1: opponent spread unknown” and later
“Game 3: earlier damage supports these ranges under the stated modifiers.” Saved game-one
analysis must never retroactively receive game-three evidence.

## Search horizon follow-up — 2026-10-13

The owner reports a newer mikumiku37 claim of looking two turns ahead. That update
has not been independently verified. The [original author post](https://www.smogon.com/forums/threads/mikumiku37-a-self-play-vgc-bot-reached-1-on-the-vgc-reg-m-c-ladder.3789199/)
describes a one-turn simultaneous matrix method, distinct from the two-turn approach
it compares against. [PKA-031](epics/e06.md#pka-031) owns the horizon/budget comparison;
[PKA-029](epics/e06.md#pka-029) establishes the initial bounded joint-action solve.
No fixed lookahead depth is chosen from the reported claim alone.
