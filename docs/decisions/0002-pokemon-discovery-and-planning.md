# ADR 0002: Champions scope and evidence-first Pokémon development

- Status: Accepted product direction; implementation choices remain conditional
- Date: 2026-10-12
- Supersedes: only the Release 0 sequencing in ADR 0001; all other platform boundaries remain

## Context

The owner approved the review's five product corrections, requested a persistent full
Kanban, selected Champions Reg C (interpreted as Regulation M-C), and accepted Showdown,
poke-env and a narrow Node bridge subject to evidence. The owner wants guided RL learning,
quality-conscious compute efficiency and main/dev/task branches. Runtime code is absent.

## Decision

A bounded simulator compatibility/rules/information study precedes implementation of
the durable execution foundation. The first real match workload then drives narrow
Core run/artifact contracts; PostgreSQL and filesystem artifacts remain candidates.
Foresight viewer usefulness does not depend on a strong learned model. Search is optional.
Champions-native stat spreads and regulations are the only model scope; Random Battles
is not a baseline/pretraining requirement. Unknown-spread replay imports are viewer-only;
additional information requires sufficient state fidelity and explicit assumptions.

Keep training/model/environment code in Arena. Lab exposes real cross-domain experiment
records rather than owning another training backend. Product identities remain branding,
not services. Track quality, assumptions, uncertainty, policy-dependent team results and
pre-decision regret. Future-regulation warm-start and PufferLib are research hypotheses.

Use the repository-local Kanban in `docs/planning/pokemon/kanban.md`, with epic cards and
one authoritative status index. The product README owns requirements. Task design,
implementation and acceptance each require the owner's explicit decisions. Plan creation
approval does not authorize application code, Git commits, paid training or publication.
Main/dev/task branch roles are documented; history and remote setup are future authorized
operations. No work moves automatically from In Review to Done.

## Alternatives

- Implement shared runtime before simulator evidence: follows the older sequence but
  risks designing contracts without known engine/data requirements.
- Build a strong RL model before any UI: delays useful inspection and couples product
  delivery to uncertain compute/generalization research.
- Adopt a trainer by advertised speed: ignores environment/IPC bottlenecks, compatibility
  and quality per cost.
- Put Pokémon training in Lab: duplicates domain ownership and cross-domain infrastructure.

## Consequences

Early experiments resolve the largest compatibility risks. The full vision is durable,
while implementation stays small and approved. The backlog is scope coverage, not a
fixed algorithm choice, deadline or claim of completion. Any conditional integration or
research result that materially changes the design returns to owner discussion.
