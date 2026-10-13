# Changelog

## Unreleased

- Added locked, standalone Champions M-C foundation probes and reports for PKA-001–003,
  covering engine/client compatibility, native rules/validator gaps and player privacy.
  All three remain In Review; no production capability or package version changes.

- Added VGC Planner as a Delphi workflow reference with Metis/Techne connections,
  documented its stated simulation assumptions, and added the unimplemented PKA-064
  review to Backlog. Recorded owner acceptance of PKA-004.
- Breaking namespace migration: `oracle-core` / `oracle_core` become
  `strixia-core` / `strixia_core`; `oracle-arena` / `oracle_arena` become
  `strixia-agon` / `strixia_agon`, both at 0.2.0. Update imports, package selections
  and local paths; no old-name aliases remain. Root metadata is `strixia-workspace`
  at 0.1.0. No runtime dependencies or functionality were added.

- Adopted Strixia / Agon / Pythia / Lyceum and Theoria / Delphi / Metis / Techne;
  moved product definitions to the accepted domain folders. Historical names and
  the external Oracle Bets project remain preserved.

- Added the owner-requested Pokémon planning board, 62 product/workflow stories,
  learning guide and version-specific PufferLib research gates.
- Recorded Champions M-C scope, collaborative approval rules, optional search,
  information-aware analysis and evidence-first sequencing in ADR 0002.
- Established local Git history and main/dev branches under PKA-004; documented
  atomic Conventional Commits, version milestones and task branches targeting dev.
  Remote setup and hosted merge requests remain pending.

## 0.1.0 scaffold — 2026-10-12

- Established Oracle Core and Arena installable package shells and Pokémon namespace.
- Configured the uv workspace, development checks, smoke tests, and CI workflow.
- Added architectural records, product definitions, and scoped Codex instructions.
- Inspected the separate Bets project and documented integration considerations.

This entry describes the local scaffold; no release, deployment, or product
implementation has been published.
