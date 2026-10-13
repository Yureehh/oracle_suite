# Champions foundation experiments

Research only, reviewed scope dated 2026-10-13: **M-C doubles, Bo3, OTS**.
These probes establish compatibility, not accuracy independently verified in the game.
These probes implement no adapter, model, trainer or application. The subsequent
[PKA-005 adapter](005-adapter.md) is a separate production capability.

- [PKA-001: simulator compatibility](001-simulator.md)
- [PKA-002: rules and legality](002-rules.md)
- [PKA-003: observations and set knowledge](003-observations.md)
- [Fixture teams](teams.json): six members each, level 50, no held items, one
  legal move per member, 66 native stat points each. Intentionally simple and
  noncompetitive; not a training corpus. Validation is mandatory before battle creation.

Run from the repository root (Node 26.0.0 and uv 0.7.5 were used):

```sh
sh scripts/pokemon_foundation/prepare.sh
uv run --project scripts/pokemon_foundation --locked python scripts/pokemon_foundation/probe.py 001 --client
uv run --project scripts/pokemon_foundation --locked python scripts/pokemon_foundation/probe.py 002
uv run --project scripts/pokemon_foundation --locked python scripts/pokemon_foundation/probe.py 003
uv run --project scripts/pokemon_foundation --locked pytest scripts/pokemon_foundation/tests
uv run --project scripts/pokemon_foundation --locked mypy --config-file scripts/pokemon_foundation/pyproject.toml scripts/pokemon_foundation/probe.py scripts/pokemon_foundation/observations.py
uv run --project scripts/pokemon_foundation --locked ruff check scripts/pokemon_foundation
uv run --project scripts/pokemon_foundation --locked ruff format --check scripts/pokemon_foundation
node --check scripts/pokemon_foundation/engine.cjs
node --check scripts/pokemon_foundation/rules.cjs
node --check scripts/pokemon_foundation/visibility.cjs
```

Preparation checks out the exact engine revision, verifies its npm lock against the
tracked copy, installs with `npm ci --omit=optional`, builds, and writes development
configuration. It installs the separately locked Python probe environment, excluded
from the root workspace. No distributable dependency changes. No upstream source
patches. The local server accepts unregistered development guests and binds only
127.0.0.1:8765; occupied ports cause failure. No credentials or public ladder are used.
The runner owns server startup/shutdown, including subprocesses, on macOS/Linux.

Results go to ignored `tmp/pokemon-foundation/<task>.json`; server logs and upstream
checkout are also ignored. Results contain privileged state and traces for research,
not policy inputs. Versions, cases and timings are machine-readable. Repeat runs
replace the corresponding result; copy to a separately named ignored run directory
if retaining multiple measurements. Checkouts must match the documented pins.

The fixtures omit optional competitive complexity. Benchmarks use deterministic
preview `1234` and engine default choices, including automatic replacements. They
measure harness throughput, not strategic strength, RL throughput or a typical metagame.
The direct batch is bounded to 100 games and 500 decision boundaries per game; the
client batch is three sets, with a 60-second deadline per set. Preparation/download
and dependency installation are excluded from execution timings.

## Verification recorded on 2026-10-13

Standalone locked sync, Ruff lint/format, strict mypy for both probe modules, all
three Node syntax checks and fifteen research tests passed. All five required root
checks passed (three installation tests, six typed package/test files). A temporary
checker verified local Markdown links/anchors/instruction paths, 65 unique cards,
existing task metadata/dependencies, dependency cycles and historical records.
Pinned Showdown tracked source remained unmodified. Local review found no remaining
actionable implementation issue; the documented simulator/client/evidence limits
remain review findings. The owner accepted all three tasks and authorized pushing/merging on 2026-10-13.
Earlier report review statuses describe the original handoff.
