# Strixia Agon — Pokémon Champions VGC

Updated: 2026-10-13

**Status:** foundation research and a local Python simulator adapter are implemented.
See the [battle guide](../../../docs/planning/pokemon/foundation/005-adapter.md).
A local durable batch worker and paired action menus are implemented.
API, website, models and analysis functionality remain unimplemented. This brief owns product requirements;
[the planning board](../../../docs/planning/pokemon/kanban.md) owns progress.

## Agreed scope and boundaries

- Initial target: Pokémon Champions Regulation M-C (“Reg C”), doubles Best-of-3 Open
  Team Sheets. Models support Champions regulations only; study native stat allocations
  and mechanics, not historical Scarlet/Violet EV/IV training or Random Battles.
- One reusable Pokémon intelligence engine. Theoria, Delphi, Metis and Techne are
  accepted product identities, not separate simulators, packages or services.
- PKA-005 uses direct pinned Showdown through a narrow Node bridge. Foundation
  research found this sufficient; poke-env remains a research dependency only.
  No custom mechanics without approval.
- Training, policies, models, evaluation and set orchestration use Python. JavaScript
  is limited to the Showdown engine boundary; it is not the training implementation.
  Hosting and process/transport optimizations follow representative profiling.
- Search is optional. Useful replay inspection precedes dependence on a strong RL model.
- Information-aware analysis and fully specified scenarios share computation but have
  different visibility contracts. Agent policies never read privileged simulator state.
- Neutral and learned/metagame scenario priors are optional assumptions. Damage/reveals
  update timestamped beliefs; knowledge may persist across Bo3 games, transient state resets.
- Explain unknown spreads in game one and evidence-supported ranges in later games.
  Do not infer exact spreads/RNG rolls from ambiguous observations or use future evidence
  to judge an earlier choice. Separate bad decisions from unlucky outcomes.
- Without supplied spreads, imported replays are viewers only. Supplied information can
  unlock facts/analysis when supported. Complete spreads alone do not establish complete
  counterfactual state; hypothetical reconstruction must be labeled.
- Display calibrated win probability only with relevant held-out evidence and explicit
  continuation conditions. Otherwise show a labeled heuristic or unavailable evaluation.
- Gauntlet results name agent pilots, opponent/team distributions and uncertainty; they
  are conditional performance evidence, not unconditional team quality.
- No paid LLMs. Explanations come from actual computation and deterministic templates.
- Build for top-quality models with measured efficiency and justified spend. Compute
  follows model/data design and pilot evidence; no paid run or strong-result promise.

## Product experiences and shared research views

Accepted product names are Theoria — Replay and decision analysis, Delphi — Matchup
exploration and preparation, Metis — Agents and learning, and Techne — Team and spread
optimization. Gauntlet, the model league, practice and coaching are features within
these products, not additional brands. [ADR 0003](../../../docs/decisions/0003-strixia-branding.md)
records the hierarchy.

| Experience | End-to-end scope | Foundation |
| --- | --- | --- |
| Theoria | Replay import/navigation, visible state, grounded evaluation timeline, alternatives and blunder review | Recorded evidence, fidelity gates, beliefs, evaluators and optional search |
| Delphi | Two-team matchup exploration, mandatory preview optimizer, alternatives, candidate payoff heatmap and on-demand flowcharts | Shared simulation/evaluation with bounded search and cache identity |
| Metis | Baselines, train → evaluate → compare → promote → reuse, regulation checkpoints, self-play and model league | Correct environment, team corpus, held-out evaluation and lineage |
| Delphi: Gauntlet | Candidate teams versus representative archetypes, intervals, weak matchups and metagame sensitivity | Same agents, set execution and stored evidence as model league |
| Metis: practice and coaching | Local battles, AI sparring and explicitly consensual assisted scrims | Same simulator, legal actions, beliefs and recommendations; shared Theoria/Delphi analysis |
| Techne | Champions stat-spread optimization, later team planning and matchup verification | Rules, breakpoint constraints and reliable conditional matchup evidence |
| Lyceum | Actual run metrics, configs, model comparisons, checkpoints and reproducibility views | Existing producer records; no separate Pokémon training backend |

Pokémon-specific training and research implementations belong under
`packages/python/strixia_agon/src/strixia_agon/pokemon/`. Thin process entrypoints belong
in apps; narrow shared lifecycle/artifact functionality belongs in Core once required.
Research protocols and decisions belong in docs; Lyceum makes their actual results visible.

## Conditional research choices

Compact policy/value representations, PPO, replay-assisted initialization, recurrent or
attention encoders, historical opponent pools, a reusable Champions base checkpoint,
PufferLib, double-oracle and deeper search require experiments. A base trained on M-C
may warm-start later regulation champions, but must beat or match fresh training under
fair budgets and demonstrate no harmful transfer. No third-party strong weights are
assumed available. Learn RL together through small explained tasks, not opaque code.

See [research choices](../../../docs/planning/pokemon/research.md),
[learning path](../../../docs/planning/pokemon/learning.md) and
[ADR 0002](../../../docs/decisions/0002-pokemon-discovery-and-planning.md).

[VGC Planner](https://vgcplanner.app/) is a product-workflow reference for Delphi's
gameplans, with future Metis suggestions and Techne preparation connections. The
[reference notes and PKA-064 review](../../../docs/planning/pokemon/research.md#vgc-gameplan-planner)
distinguish observed UX, author-documented behavior and proposed adaptations. Its
chance/mechanics assumptions do not replace our simulator and fidelity requirements.

## Delivery and deferred capabilities

The roadmap first proves compatibility, then legal recorded Bo3 execution, useful
web inspection, evidence-aware analysis, trainable models and preparation tools.
2026 scope is provisional until actual availability/compute and pilot results are
known. No mandatory long-term feature is dropped by that bounded near-term target.

Decision puzzles, spectator mode, public bots, advanced weakness tracking, metagame
views, additional formats and broad automated team planning remain deferred. Other
Agon games are outside this Pokémon backlog. Public releases need separate approval,
actual authorization/privacy boundaries and an agreed licensing/asset policy.

## Collaboration

Every application task follows Propose → Discuss → Approve → Implement → Test → Review
→ Confirm. Scope-plan approval is not code approval. Explain concepts as needed and
compare options at each research gate. Maintain main/dev/task-branch workflow once its
setup is authorized. No automatic next task, commit, push, spending or release.
