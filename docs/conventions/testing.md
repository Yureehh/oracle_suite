# Testing

The current tests verify installed distribution metadata, package imports, the
Pokémon namespace, native input guards, player information boundaries, paired choices,
simulator rollback and local run/artifact persistence. Real-engine tests need the
pinned Showdown checkout prepared first; CI prepares it before testing. The separate
foundation probe has its own tests and lock. Tests do not establish actual-game fidelity
or ML quality. No root pytest
`pythonpath` setting masks installation failures. Importlib discovery permits package
scopes without adding `__init__.py` to every tests directory.

Run `uv sync --locked --all-packages`, then
`uv run --locked --all-packages pytest` from the root. CI runs the same checks as
[local development](../runbooks/local-development.md). Tests belong beside their owning
package and must be included in root discovery when a new package is introduced.

Test contracts, edge cases, error paths and restart recovery.
Use small reviewed fixtures under `tests/fixtures/`, not root generated data. Seed
stochastic tests and distinguish determinism from statistical guarantees. Keep slow
integration/training tests explicit; introduce markers only when needed.

Test real mechanics against external rules and trusted examples. Compare models
against defined baselines with time/ruleset-appropriate splits. Do not add a coverage
percentage target for empty shells or tests that simply mirror implementation.
Benchmarks should be separate from correctness gates, with workload and hardware
recorded. An unexecuted CI run is not a passing check.

## Audit cadence

Use focused reviews for individual changes. Run a whole-repository Ponytail audit
after an epic milestone or roughly three to five completed behavioral stories,
before substantial training or a public release, and after major simulator,
observation, action or persistence changes. Record the inspected commit, findings,
reproductions and remaining limits in a dated report under `docs/audits/`. Track
follow-up scope and the next trigger in [PKA-067](../planning/pokemon/epics/e01.md#pka-067);
an audit report does not itself authorize repairs or publication.
