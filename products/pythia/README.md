# Strixia Pythia

Pythia is Strixia's predictive intelligence domain: probabilistic forecasts, evaluation,
historical analysis and research workflows. It already has separate development work.
No Pythia package or application is created in this scaffold.

## Inspected existing project

On 2026-10-12, a read-only inspection found `/Users/yureeh/dev/oracle_bets`.
Its Git worktree was clean. The inspection read its README, pyproject, Python pin,
CI configuration, package/test inventory, and representative contracts/path code.
It did not run/import its code, read secrets or private datasets, or verify its model
results. The observed structure is:

```text
oracle_bets/
├── pyproject.toml, uv.lock, .python-version, LICENSE
├── packages/
│   ├── oracle-bets-core/src/oracle_bets_core/
│   ├── lol-bets/src/lol_bets/
│   └── oracle-bets-discord/src/oracle_bets_discord/
├── config/
├── tests/core/ and tests/lol/
├── docs/ and mkdocs.yml
├── ops/launchd/
├── data/, models/, reports/, logs/, notebooks/
└── .github/workflows/ci.yml
```

Its root metadata declares one `oracle-bets` distribution built with setuptools,
collecting sources from the three package directories; these are not three independently
configured uv workspace members. It requires Python >=3.12 and pins the 3.12 line.
The CLI entrypoint is `oracle_bets_core.cli:main`. Dependencies include pandas, NumPy,
scikit-learn, LightGBM, Optuna, rating libraries, plotting, requests and python-dotenv.
Its dev extra uses pytest, Ruff, ty and MkDocs; optional extras cover Discord and AI
review. It has its own lockfile and an Apache-2.0 license declaration.

The README describes LoL ingestion, chronological features, calibrated forecasting,
market review, paper evidence and owner-controlled Discord workflows. Those descriptions
are existing-project claims, not fresh runtime validation. Source inspection confirmed
artifact-health contracts and filesystem configuration. `paths.py` reads environment
settings and eagerly creates storage directories, including an evidence database path
at `data/state/oracle_bets.db`; it was deliberately not imported during inspection.
No data schema or performance claim is inferred from these path names.

## Integration direction

Keep the separate repository and runtime intact until a dedicated integration task.
Inventory its real CLI, data ownership, storage/migration behavior, model lifecycle,
package boundaries and regression checks before moving anything. Compare its current
lockfile and ML requirements against Strixia's workspace resolution; Python alignment
alone does not demonstrate dependency compatibility. Its existing ty workflow need
not be replaced just because this scaffold uses mypy.

Use documented result metadata or an explicit adapter as the first integration boundary
when a real consumer exists. Preserve its canonical datasets, evidence, model registry,
configuration and history. Keep its existing Bets Core distinct from `oracle_core`;
extract shared behavior only after actual interfaces and consumers are understood.
Do not simply copy sources and rename packages or merge databases.

Resolve licensing for the combined repository with the owner; Bets's existing license
does not authorize assigning a new license to Strixia. This inventory is a snapshot,
not a second product specification: refer to the actual Bets docs for authoritative
behavior. Core reuse and Lyceum views should follow compatible real run/artifact interfaces.

Open decisions: integration timing, source/history strategy, dependency isolation,
interface compatibility and license reconciliation. Migration and new forecasting
features are deferred. No existing Bets files were changed by bootstrap.
