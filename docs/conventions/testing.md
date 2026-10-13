# Testing

The current tests verify installed distribution metadata, package imports and the
Pokémon namespace. They do not validate simulator behavior or ML results. No pytest
`pythonpath` setting masks installation failures. Importlib discovery permits package
scopes without adding `__init__.py` to every tests directory.

Run `uv sync --locked --all-packages`, then
`uv run --locked --all-packages pytest` from the root. CI runs the same checks as
[local development](../runbooks/local-development.md). Tests belong beside their owning
package and must be included in root discovery when a new package is introduced.

As behavior arrives, test contracts, edge cases, error paths and restart recovery.
Use small reviewed fixtures under `tests/fixtures/`, not root generated data. Seed
stochastic tests and distinguish determinism from statistical guarantees. Keep slow
integration/training tests explicit; introduce markers only when needed.

Test real mechanics against external rules and trusted examples. Compare models
against defined baselines with time/ruleset-appropriate splits. Do not add a coverage
percentage target for empty shells or tests that simply mirror implementation.
Benchmarks should be separate from correctness gates, with workload and hardware
recorded. An unexecuted CI run is not a passing check.
