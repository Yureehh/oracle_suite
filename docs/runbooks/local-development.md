# Local development

Open the repository root (`/Users/yureeh/dev/oracle_suite` in the bootstrap workspace).
Install uv following its [official guide](https://docs.astral.sh/uv/getting-started/installation/)
if missing; no manual virtualenv activation is needed. Validation uses uv 0.7.5.

```bash
uv --version
uv python install 3.12
uv sync --locked --all-packages --extra learning
uv run --locked --all-packages pre-commit install
uv run --locked --all-packages pre-commit run --all-files
uv run --locked --all-packages ruff check .
uv run --locked --all-packages ruff format --check .
uv run --locked --all-packages mypy
uv run --locked --all-packages pytest
uv build --package strixia-core
uv build --package strixia-agon
```

`uv python install` manages Python; `.python-version` selects the 3.12 line. Initial
package installs are editable. `--locked` checks that metadata matches `uv.lock`;
`--all-packages` includes both libraries in the root environment. mypy targets
source and tests explicitly, and pytest discovers package and worker tests without
manually setting PYTHONPATH. Build outputs go to ignored `dist/` and are never published.

If the lockfile is stale after an intentional dependency change, run `uv lock`, review
the diff, then sync again. Do not use `--frozen` to hide stale metadata. Format with
`uv run --locked --all-packages ruff format .` and rerun the applicable checks.

`.env.example` has no mandatory variables; the local batch coordinator needs no server.
Development needs package-index access on a cold cache.
Missing network/tools must be reported as limitations, not success. When runtime
applications arrive, document each process command, its dependencies and recovery path.

## Local Champions game

```bash
sh scripts/pokemon_foundation/prepare.sh --engine-only
uv run --locked --all-packages python scripts/pokemon_battle.py
```

Requires Node and Git. See the [battle guide](../planning/pokemon/foundation/005-adapter.md).
Integration tests skip without the built engine; CI prepares it before tests.

## Durable independent-game batches

See the [local batch runbook](local-batches.md) for submission, parallel execution,
status, explicit resume and export. It uses local SQLite and files, with no installed
server database. Root checks include the worker's tests and type checking.

## Commit hooks

Hooks run on staged files; use `pre-commit run --all-files` through the locked uv
workspace for a full check. Ruff uses the same locked version locally and in CI.
The standard file hooks use a pinned upstream revision and isolated environments;
the first run downloads them. No tests or type checker run during each commit.
A fresh clone needs `pre-commit install`; Git does not clone installed hooks.

Full source typing and model checks require the optional `learning` extra. CI installs
it explicitly. A simulator-only installation can omit it; optional Torch tests skip
there, while observation construction remains available without Torch.
