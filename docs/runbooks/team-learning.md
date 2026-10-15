# Team corpus and single-game learning interface

PKA-035 provides frozen local team data. PKA-037 provides a Python interaction loop;
no neural network, optimizer, trainer or PufferLib adapter is implemented.

## Build a corpus

```bash
uv run --locked --all-packages python scripts/pokemon_corpus.py tmp/team-corpus/new-snapshot
```

This reads the explicitly labeled Champions M-C tab of the owner's VGCPastes source.
Use `--csv <captured-source.csv>` to reuse a captured source index and
`--imports <captured-imports-directory>` to rebuild entirely from captured parsed
inputs without new network requests. The pinned validator is still required.
Four bounded fetch workers retrieve PokePastes; engine validation runs in source order. Output
must be a new ignored directory. The script creates files exclusively and refuses
to replace an existing snapshot. It performs no battles or model training.
An interrupted/failed build may retain a partial directory for diagnosis. Only a
completed `corpus.json` is a usable corpus; rebuild into a new directory rather
than overwrite partial artifacts. Automatic collection recovery is not implemented.

The snapshot contains the original source CSV, parsed source imports, an inventory
with admission/rejection reasons and a native `corpus.json` manifest. Entries
without claimed spreads stay in the inventory; even entries marked complete must
supply all required fields and pass pinned-engine M-C validation. No spread is
invented. Owner-authored and extracted paste provenance stays distinct. Cosmetic
and legacy mechanic annotations remain in the import and are inactive in M-C.

Team identity includes species, gender, ability, item, moves, nature and allocations.
Validated move aliases/casing are canonicalized through the pinned engine data.
Slot and move ordering do not create a new team identity. Exact duplicates retain
all source references; spread/move variants remain separate teams. The same sorted
six-species composition is only an evaluation grouping key. Normalized Mega/base
forms follow the pinned validator and preserve the original imported form separately.

Sort composition groups by SHA-256 and allocate 70%/15%/remaining groups to training,
validation and test, rounding down the first two counts while retaining at least
one group per split. Fewer than three groups is an error. Ratios apply to groups,
not team counts. Near-identical five-of-six teams and shared events can still cross
partitions; broader archetype/event holdouts require later evaluation design.
The manifest's content ID covers its schema, ruleset/engine pin, source CSV hash,
normalized teams, provenance and split assignments. Group assignment is frozen per
snapshot; new source snapshots can change rank-based assignments, so compare runs
using the same frozen manifest rather than mixing snapshots.

Sources are public references for local research; no redistribution license was
established and no source dataset is committed. [Pick Four](https://pickfour.win/meta)
is a discovery/coverage reference, not an automatic source of known spreads: its
[methodology](https://pickfour.win/method) documents generated allocations and mixed
set sources. Such assumptions are excluded from this first known-spread corpus.

## Exercise the environment

```bash
uv run --locked --all-packages python scripts/pokemon_environment.py --games 2
uv run --locked --all-packages python scripts/pokemon_environment.py --corpus tmp/team-corpus/new-snapshot/corpus.json --split test --games 10 --seed 123
```

The first command uses research fixtures. The second samples complete teams from
one frozen corpus split and runs existing seeded random policies. It is an
interaction smoke test, not an estimate of agent strength. `--games` is bounded
from 1 to 100; this demonstration runs games sequentially. Each environment owns
one existing Node engine process; future parallel collectors must own separate
instances. Transport/performance work belongs to measured PKA-039/045 experiments.

`ChampionsEnv(checkout, decision_limit=500, retry_limit=16)` supports:

- `reset(teams, seed)` starts a fresh single-game episode with six-member teams and
  returns two separate immutable player views. Seed and opponent private state
  stay outside policy observations.
- `observe(player)` and `actions(player)` provide that player's view and complete
  legal joint-action menu. A model selects a menu index; it does not independently
  choose incompatible slot actions. Tensor encoding and model design are PKA-038.
- `step(p1_index, p2_index)` submits both choices before resolving the engine. Its
  immutable transition contains the two player observations, rewards, `terminated`
  and `truncated`. This pair is for the trusted collector; each policy gets only
  its own view/menu. Waiting requests use the singleton waiting menu.
- Known-invalid indices fail before engine submission. A hidden restriction may
  raise `RequestUpdatedError`: no learning transition occurred. Refresh only the
  player whose view changed, retaining the other's selected index. Retries are
  bounded per decision; engine errors raise rather than becoming losses.
- Normal outcomes reward the winner +1 and loser -1, with 0 for draws and ordinary
  intermediate steps. Finishing on the last allowed decision is termination.
  Exhausting the limit in a live game is truncation with 0 outcome reward and a
  retained nonterminal observation for future value bootstrapping; it is not a draw.
- `close()` or context exit releases the engine. A terminal/truncated episode needs
  reset before further steps; a failed reset cannot expose the previous game.

Potential-based reward shaping will be compared against canonical outcomes in
PKA-040 under equal budgets and held-out win-rate evaluation. Reward scaling alone
does not solve delayed feedback; arbitrary KO bonuses can change the objective.
No shaping scheme is claimed beneficial before measurement. Bo3 learning episodes
are separately tracked in PKA-069; current gameplay/scoring already supports Bo3.

## Measured delivery snapshot (2026-10-14)

`tmp/team-corpus/mc-2026-10-14-canonical/corpus.json` contains 545 distinct
validated teams from 554 accepted source entries. The source has 647 entries: 87
without claimed spreads and six invalid/incomplete entries excluded with reasons.
The 436 composition groups split 305/65/66, giving 377/77/91 individual teams.
Corpus ID: `fde5c921dcc9124dc189b0a8b57d5ca019dffb7bb6cc866b6d0238afddba8e93`.
Ten held-out-team demonstration games all terminated, including both winner sides
and two request refreshes. This establishes interface compatibility with those
samples, not actual-game parity or learning quality.

Delivery checks passed: locked workspace sync, Ruff lint/format, strict mypy,
96 pytest cases, pre-commit and Node syntax. Agon 0.6.0 built as sdist/wheel;
a fresh isolated wheel validated a fixture team and completed a seeded game.
Corpus content identity, exact-team uniqueness and composition split isolation
were checked. Full CE review `20261014-153959-b3e2250d` completed with no unresolved
findings. Its cross-model transport was unavailable; the adversarial lens used a
local fallback. Stories remain In Review pending owner acceptance.
