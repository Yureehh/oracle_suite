# Local development

Open the repository root (`/Users/yureeh/dev/oracle_suite` in the bootstrap workspace).
Install uv following its [official guide](https://docs.astral.sh/uv/getting-started/installation/)
if missing; no manual virtualenv activation is needed. Validation uses uv 0.7.5.

```bash
uv --version
uv python install 3.12
uv sync --locked --all-packages
uv run --locked --all-packages ruff check .
uv run --locked --all-packages ruff format --check .
uv run --locked --all-packages mypy
uv run --locked --all-packages pytest
uv build --package oracle-core
uv build --package oracle-arena
```

`uv python install` manages Python; `.python-version` selects the 3.12 line. Initial
package installs are editable. `--locked` checks that metadata matches `uv.lock`;
`--all-packages` includes both library shells in the root environment. mypy targets
source and tests explicitly, and pytest discovers both test directories without
manually setting PYTHONPATH. Build outputs go to ignored `dist/` and are never published.

If the lockfile is stale after an intentional dependency change, run `uv lock`, review
the diff, then sync again. Do not use `--frozen` to hide stale metadata. Format with
`uv run --locked --all-packages ruff format .` and rerun the applicable checks.

There is no server to start or service to configure. `.env.example` documents conventions
and has no mandatory variables. Development needs package-index access on a cold cache.
Missing network/tools must be reported as limitations, not success. When runtime
applications arrive, document each process command, its dependencies and recovery path.
