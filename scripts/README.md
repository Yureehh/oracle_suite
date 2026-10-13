# Development scripts

Run `pokemon_battle.py` for one Python-controlled Champions game. See the
[battle guide](../docs/planning/pokemon/foundation/005-adapter.md) for setup and inputs,
and the [local development runbook](../docs/runbooks/local-development.md) for checks.

Add a script only when repeated real work is clearer than a documented tool command.
Keep it portable, scoped, explicit about inputs and side effects, and independent of
local secrets or absolute machine paths. Do not add automated game scaffolding,
migration scripts or workload runners before their use cases exist.

The [standalone Pokémon foundation probes](pokemon_foundation/README.md) implement
the approved PKA-001–003 research batch; their dependencies are isolated from the
root workspace and distributable packages.
