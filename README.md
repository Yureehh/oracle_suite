# Oracle

Oracle is a Python-first platform for AI engineering and research: reinforcement
learning, game theory, search, simulation, probabilistic prediction, and reproducible
experiments. Its mission is to turn rigorous computational work into useful tools
through one eventual web experience.

**Status: repository scaffold.** Only package installation, development tooling,
smoke tests, and documentation exist here. There is no API, worker, frontend,
simulator, trained model, database, or experiment tracker yet.

## Platform

- **Arena:** competitive game AI. Pokémon VGC is the first flagship; Magic: The
  Gathering and Poker are future possibilities.
- **Bets:** probabilistic forecasting and evaluation. A separate existing project
  was inspected; it remains unchanged and outside this workspace. See its
  [inventory and integration plan](products/bets/README.md).
- **Lab:** future cross-domain views of real runs, metrics, and artifacts produced
  by workloads. It will reuse their experiment infrastructure.
- **Core:** narrowly shared infrastructure, introduced only for demonstrated needs.
  The current package contains no runtime functionality.

Pokémon product names Foresight, Delphi, Augur, and Forge are provisional branding,
not package or service boundaries. A common game engine should serve future products.

## Repository map

```text
oracle_suite/
├── README.md, AGENTS.md, CONTRIBUTING.md, CHANGELOG.md
├── pyproject.toml, uv.lock, .python-version
├── .gitignore, .gitattributes, .editorconfig, .env.example
├── apps/
│   ├── api/       # future backend entrypoint; README and scoped instructions
│   ├── web/       # future website; README and scoped instructions
│   └── worker/    # future execution process; README and scoped instructions
├── packages/python/
│   ├── oracle_core/  # pyproject, README, AGENTS, src/oracle_core, tests
│   └── oracle_arena/ # pyproject, README, AGENTS, src/oracle_arena/pokemon, tests
├── products/
│   ├── arena/pokemon/ # product vision and constraints
│   ├── bets/          # existing-project inventory and future integration
│   └── lab/           # cross-domain research visibility
├── docs/
│   ├── architecture/ # overview, boundaries, deployment
│   ├── decisions/    # architecture decision records
│   ├── conventions/  # Python, testing, research, documentation
│   └── runbooks/      # local development
├── infra/            # infrastructure guidance; no provisioned services
├── scripts/          # automation policy; no scripts needed yet
└── .github/workflows/ci.yml
```

The directory is named `oracle_suite` by owner choice; it is the Oracle repository
root. `products/` owns product definitions, `packages/python/` owns reusable code,
and `apps/` owns executable application boundaries. `docs/` owns engineering guides.

## Technology choices

| State | Technologies |
| --- | --- |
| Configured | Python 3.12 baseline, uv workspace and lockfile, uv_build, Ruff, mypy, pytest, GitHub Actions |
| Architectural preferences | FastAPI API, TypeScript/React/Next.js website, Python worker, one website |
| Candidates for the first workload | PostgreSQL durable metadata/task claims, local filesystem artifacts |
| Deferred options | Containers, object storage, GPU execution and model serving when measured needs justify them |

No runtime third-party dependencies are installed by either library. Development
tools belong to the root dependency group; future ML dependencies belong to their
owning package or workload extra. CI exercises Python 3.12; later Python versions
are allowed by metadata but not yet verified.

## Getting started

No remote is configured. Open this local checkout:

```bash
cd /Users/yureeh/dev/oracle_suite
```

After a remote is chosen, clone its actual URL and open the resulting directory.
Do not use a guessed repository URL. Install uv using the
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
builds, use `uv build --package oracle-core` and `uv build --package oracle-arena`.
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

The subsequent milestone is Oracle Release 0: a small durable Run lifecycle, API and
worker, metadata, and artifacts, then the first genuine Pokémon Arena workload.
Define its states, failure recovery, and acceptance tests before implementation.
The [Pokémon product brief](products/arena/pokemon/README.md) records the agreed vision;
individual implementation designs still require discussion and approval. Later work can add verified
research results, Lab views backed by those results, and a public web experience.
There are no promised release dates or performance claims.

## License

Licensing remains undecided. No public-source license is granted by this scaffold.
The separate Bets project's license does not automatically license this repository.
