# PKA-005: Python-controlled Champions game

Implemented 2026-10-13 in strixia-agon 0.3.0. This is one local M-C doubles game,
not a trainer or a complete Bo3 runner. Python owns orchestration and future policies;
Node runs the pinned Showdown engine through stdin/stdout, with no listening server.

## Run it

From the repository root, install Node and Git, then:

```bash
sh scripts/pokemon_foundation/prepare.sh --engine-only
uv sync --locked --all-packages
uv run --locked --all-packages python scripts/pokemon_battle.py
uv run --locked --all-packages pytest packages/python/strixia_agon/tests/test_simulator.py
```

Preparation downloads and builds Showdown in ignored `tmp/` using the reviewed npm
lock. It does not install poke-env. Tested runtimes: Python 3.12.13 and Node 26.0.0;
engine revision `3a766f2cfb5e51c1e428cfe87d0dba91a8f01640`.
The demo selects four of six and uses engine-default choices. Those choices exercise
execution; they are not a random or strategic policy. The default fixtures are small,
reviewed compatibility teams, not competitive training data. Default seed 1,2,3,4
finishes on turn 4 with p1 winning.

## Teams and Python boundary

Code lives in `strixia_agon.pokemon.simulator`. Construct two six-member lists of
`TeamMember`, then use `ChampionsBattle(checkout_path, teams, (1, 2, 3, 4))` as a
context manager. `battle.state.view("p1")` supplies only p1's typed player view.
`battle.step("team 1234", "team 1234")` completes preview; subsequent calls submit
both players' coordinated engine choice strings. Use `None` when that player's
view says `must_wait`. Legal action enumeration belongs to PKA-006.

The demo also accepts `--teams /absolute/path/teams.json`. The JSON is a list of two
six-member lists, with this shape for each member (this example alone is not a team):

```json
{
  "species": "Charizard", "ability": "Blaze", "moves": ["Heat Wave"],
  "nature": "Modest", "item": "", "gender": "M",
  "stat_points": {"hp": 2, "atk": 0, "def": 0, "spa": 32, "spd": 0, "spe": 32}
}
```

Python rejects noninteger points, values outside 0–32 and totals above 66. Points
map directly to the engine's historically named `evs` fields: no legacy conversion.
Level is 50 and engine IV fields use the verified sentinel 31. Showdown validates
both complete teams before simulation and preserves rejection reasons. Any team
accepted by this pinned M-C validator may be supplied; game fidelity limitations
remain those documented in [the rules report](002-rules.md).

## Guarantees and limits

One Node process stays alive across decisions within a game. Context exit releases
it; process failure, malformed replies and response timeout raise `SimulatorError`.
Rejected action pairs raise `InvalidChoiceError`, restoring the previous decision
boundary so Python can correct and retry. Restoration here supports rejection
handling; a public branching/search API remains PKA-009.

Player views contain shared protocol history, actual opponent team-sheet fields,
current own Pokémon and own action requests. They exclude opponent stats, RNG,
queued simultaneous choices and snapshots. The trusted controller holds both private
views; give a policy only its own view. These immutable records are not RL tensors
or a hardened security sandbox. Wall-clock protocol markers are omitted so identical
teams, engine, seeds and choices yield identical histories. Old views stay unchanged.

Tests cover seeded replay, natural completion, forced replacements, invalid choices,
validator rejection, hidden-world projection, malformed/failed/timed-out processes
and cleanup. Engine integration tests skip when the checkout is absent; CI prepares
it and must run them. Training throughput is unmeasured: Python/Node communication
has a cost, to be benchmarked with real workloads before choosing batching or hosting.
