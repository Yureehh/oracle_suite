# Strixia

Strixia is a Python-first platform for AI engineering and research: reinforcement
learning, game theory, search, simulation, probabilistic prediction, and reproducible
experiments. Its mission is to turn rigorous computational work into useful tools
through one eventual web experience.

**Status: first local simulation capability.** Agon 0.4.0 provides player-visible paired choices for a pinned Champions
M-C game. Core 0.3.0 and a local Python worker persist batches in SQLite and files,
with bounded parallel games and explicit resume. There is no API, frontend, trained
model or experiment tracker yet.
See the [battle guide](docs/planning/pokemon/foundation/005-adapter.md) and
[durable batch runbook](docs/runbooks/local-batches.md).

## Platform

- **Agon:** competitive game AI. Pokémon VGC is the first flagship; Magic: The
  Gathering and Poker are future possibilities.
- **Pythia:** probabilistic forecasting and evaluation. A separate existing project
  was inspected; it remains unchanged and outside this workspace. See its
  [inventory and integration plan](products/pythia/README.md).
- **Lyceum:** future cross-domain views of real runs, metrics, and artifacts produced
  by workloads. It will reuse their experiment infrastructure.
- **Core:** narrowly shared infrastructure, introduced only for demonstrated needs.
  The package now supplies run records and immutable artifacts for the local worker.

Pokémon products are **Theoria — Replay and decision analysis**, **Delphi — Matchup
exploration and preparation**, **Metis — Agents and learning**, and **Techne — Team
and spread optimization**. These names are accepted branding, not package or service
boundaries. A common game engine should serve future products. See
[ADR 0003](docs/decisions/0003-strixia-branding.md) for the naming and migration policy.

## Repository map

```text
oracle_suite/
├── README.md, AGENTS.md, CONTRIBUTING.md, CHANGELOG.md
├── pyproject.toml, uv.lock, .python-version
├── .gitignore, .gitattributes, .editorconfig, .env.example
├── apps/
│   ├── api/       # future backend entrypoint; README and scoped instructions
│   ├── web/       # future website; README and scoped instructions
│   └── worker/    # local durable batch coordinator; README and scoped instructions
├── packages/python/
│   ├── strixia_core/  # pyproject, README, AGENTS, src/strixia_core, tests
│   └── strixia_agon/ # pyproject, README, AGENTS, src/strixia_agon/pokemon, tests
├── products/
│   ├── agon/pokemon/  # product vision and constraints
│   ├── pythia/        # existing-project inventory and future integration
│   └── lyceum/        # cross-domain research visibility
├── docs/
│   ├── architecture/ # overview, boundaries, deployment
│   ├── decisions/    # architecture decision records
│   ├── conventions/  # Python, testing, research, documentation
│   └── runbooks/      # local development
├── infra/            # infrastructure guidance; no provisioned services
├── scripts/          # local battle demo and isolated foundation probes
└── .github/workflows/ci.yml
```

The directory is named `oracle_suite` by owner choice; it is the Strixia repository
root. `products/` owns product definitions, `packages/python/` owns reusable code,
and `apps/` owns executable application boundaries. `docs/` owns engineering guides.

## Technology choices

| State | Technologies |
| --- | --- |
| Configured | Python 3.12 baseline, uv workspace and lockfile, uv_build, Ruff, mypy, pytest, GitHub Actions |
| Architectural preferences | FastAPI API, TypeScript/React/Next.js website, Python worker, one website |
| Implemented local workload | SQLite metadata, immutable filesystem artifacts, bounded parallel Python coordinator |
| Future candidates | PostgreSQL metadata on RDS/Aurora, shared artifact storage when needed |
| Deferred options | Containers, object storage, GPU execution and model serving when measured needs justify them |

No runtime third-party dependencies are installed by either library. Development
tools belong to the root dependency group; future ML dependencies belong to their
owning package or workload extra. CI exercises Python 3.12; later Python versions
are allowed by metadata but not yet verified.

## Getting started

The configured remote is [Yureehh/oracle_suite](https://github.com/Yureehh/oracle_suite).
The repository URL and local checkout name remain unchanged by the branding migration.
Open this local checkout:

```bash
cd /Users/yureeh/dev/oracle_suite
```

For another checkout, clone the configured URL and open the resulting directory.
Install uv using the
[official installation guide](https://docs.astral.sh/uv/getting-started/installation/).
On macOS/Linux the documented installer is:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Open a new shell if needed, then run from the repository root:

```bash
uv --version
uv python install 3.12
uv sync --locked --all-packages
uv run --locked --all-packages ruff check .
uv run --locked --all-packages ruff format --check .
uv run --locked --all-packages mypy
uv run --locked --all-packages pytest
```

No virtual environment activation is required. Always include `--all-packages`
for root checks: it installs the workspace members without inventing root runtime
dependencies. `--locked` rejects stale dependency declarations rather than silently
changing the lockfile. The scaffold is validated with uv 0.7.5, also pinned in CI;
a newer uv can be used after checking lockfile compatibility.

For formatting, use `uv run --locked --all-packages ruff format .`. For package
builds, use `uv build --package strixia-core` and `uv build --package strixia-agon`.
Builds remain local and do not publish distributions.

## Development and roadmap

Read [CONTRIBUTING.md](CONTRIBUTING.md), the
[boundaries](docs/architecture/boundaries.md), and relevant scoped `AGENTS.md`
before substantial changes. Put a product specification in its existing product
directory; implement reusable logic in its owning library. Introduce a new package
only when dependencies or ownership require it. See the
[new-product procedure](CONTRIBUTING.md#adding-a-product).

The [Pokémon planning board](docs/planning/pokemon/kanban.md) captures the agreed full
product scope and task approval workflow. A bounded Champions simulator compatibility
study now precedes runtime implementation, as recorded in
[ADR 0002](docs/decisions/0002-pokemon-discovery-and-planning.md).

The subsequent milestone is Strixia Release 0: a small durable Run lifecycle, API and
worker, metadata, and artifacts, then the first genuine Pokémon Agon workload.
Define its states, failure recovery, and acceptance tests before implementation.
The [Pokémon product brief](products/agon/pokemon/README.md) records the agreed vision;
individual implementation designs still require discussion and approval. Later work can add verified
research results, Lyceum views backed by those results, and a public web experience.
There are no promised release dates or performance claims.

## License

Licensing remains undecided. No public-source license is granted by this scaffold.
The separate Oracle Bets project's license does not automatically license this repository.
