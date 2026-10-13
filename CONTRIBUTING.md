# Contributing

This scaffold has no public-source license yet. Confirm contribution and licensing
terms with the owner before distributing code. Never commit credentials or generated
research outputs.

## Making a change

Read root and applicable scoped instructions, relevant product definitions, and
[architecture decisions](docs/decisions/0001-monorepo-architecture.md). Inspect the
current code before proposing a replacement. Define expected behavior and how to
verify it. Keep changes tied to one concrete requirement; do not fill empty modules
with speculative contracts. Preserve existing work and document meaningful tradeoffs.

Use Python 3.12 and the root uv workspace. Add runtime dependencies with
`uv add --package <package-name> <dependency>`; add tools with
`uv add --group dev <tool>`. Update and review `uv.lock` whenever dependencies change.
Install the local commit hooks after syncing the workspace:

```bash
uv sync --locked --all-packages
uv run --locked --all-packages pre-commit install
uv run --locked --all-packages pre-commit run --all-files
```

Hooks check file syntax, merge markers, files over 500 KiB, private keys and
whitespace, then run Ruff lint fixes and formatting using the workspace lock.
If a hook changes a file, review and stage that change before committing again.
CI runs the same hook suite; new clones must install the Git hook themselves.
Keep mypy and simulator tests in the full checks below rather than every commit.

Before submitting a change:

```bash
uv sync --locked --all-packages
uv run --locked --all-packages ruff check .
uv run --locked --all-packages ruff format --check .
uv run --locked --all-packages mypy
uv run --locked --all-packages pytest
```

Add behavior tests for real functionality. Record measured performance evidence
when optimizing. Update affected docs and the Unreleased changelog. State any checks
that could not run; do not treat unexecuted CI as passing.

## Commits and versions

The owner selected frequent, small atomic commits on 2026-10-13. Within an explicitly
approved implementation task, local commits of its owned changes are authorized.
Task approval does not authorize unrelated files, merges, pushes, tags or publication.
The owner approved the initial baseline snapshot and branch setup under PKA-004 on
2026-10-13. This initialization is the exception to committing on task branches.

One commit should express one coherent change and include its necessary tests and
configuration. Commit after a meaningful checked step; do not split working code from
its required tests just to increase commit count. Stage exact owned paths, review the
staged diff, and never absorb someone else's index or unrelated untracked files.
Record checks in the task review. Preserve useful atomic commits through integration;
do not routinely squash them into a single large feature commit.

Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):

```text
feat(agon): validate coordinated switch choices
fix(core): recover an interrupted run claim
docs(pokemon): explain player information boundaries
```

Use `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `build`, `ci` or `chore` as
appropriate. Add `Refs: PKA-001` in the footer for tracked work. Mark incompatible
changes with `!` or a `BREAKING CHANGE:` footer and explain the migration.

Package versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
During 0.x development, this repository's policy is patch bumps for meaningful
compatible fixes and minor bumps for completed capabilities or incompatible contracts.
Document incompatible changes even before 1.0. After 1.0, incompatible public contracts
require a major bump. Bump once per accepted capability/fix milestone, not every commit;
documentation, tests alone and behavior-preserving cleanup do not require a bump.

Version only affected distributable packages. Keep package metadata, lockfile,
installation expectations and changelog consistent in the same version-change commit.
The non-distributable root workspace version is not a platform release counter.
Model/checkpoint IDs and regulation lineage are independent of Python package versions.
The renamed distributable shells are 0.2.0 for their incompatible import names;
the non-distributable root metadata remains 0.1.0. Branding adds no runtime capability.
Keep changes under Unreleased until a release is actually approved. No tags or release
automation now; future tags identify approved reproducible releases.

## Adding a product

1. Write the canonical specification under `products/<domain>/<product>/`; link to
   it from architecture docs rather than copying its requirements.
2. For another Agon game, start with game-specific code under `strixia_agon` when
   that package fits. Do not force Pokémon observations or actions onto Magic.
3. Split into a new `src/` package only for demonstrated ownership, dependency, or
   runtime isolation needs. Add its exact path to workspace members and include its
   source/tests in type checking and pytest discovery.
4. Reuse Core capabilities only if actual interfaces fit. Core is not a collection
   of every helper with similar names.
5. Add scoped coding rules for game mechanics, information boundaries and versioning;
   make the root instruction index point to them.
6. Add thin API routes under `apps/api` only once a use case needs them; delegate
   expensive work to workers and validate external inputs.
7. Add routes to the eventual shared website under `apps/web`. Product branding
   must not create duplicated engines or independent services by default.
8. Test mechanics, determinism, failures, and evaluation methodology. Benchmark
   representative workloads and record uncertainty and reproducibility metadata.
9. Record consequential architectural choices in an ADR and update status docs.

The external Oracle Bets project requires a separate Pythia integration plan based
on its inspected implementation.
Its migration, license reconciliation, dependency resolution, data handling, and
regression testing are outside this bootstrap.
