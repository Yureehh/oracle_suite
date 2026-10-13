# Arena rules

Keep game rules and mechanics domain-specific. Separate environments, policies,
evaluation and training conceptually; create modules only when code needs them.
Treat simulator correctness as critical and support deterministic tests where possible.
Track environment and ruleset versions with research results.

Do not assume a model transfers between games or impose universal observation/action
schemas without real reuse. Prefer reproducible benchmarks to anecdotal claims.
Keep agents independent of presentation. Read the Pokémon-specific code and product
instructions when working on Pokémon. No game implementation is part of bootstrap.
