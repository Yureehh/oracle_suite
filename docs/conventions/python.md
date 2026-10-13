# Python standards

Use Python 3.12 as the tested baseline and consistent `requires-python = ">=3.12"`
metadata. Libraries use `src/` layouts. Prefer modern annotations, pathlib, explicit
errors and standard-library utilities. Write PEP 257-style docstrings for public
behavior where useful. Ruff formats PEP 8-compatible code at 88 columns and checks
imports, common errors, modern syntax and selected bug patterns; it does not enable
all rules for appearance. mypy strict checks source and tests without broad suppressions.

Runtime dependencies belong to their owning package, added with `uv add --package`.
Tools belong to the root dev dependency group. Training extras are appropriate when
heavy dependencies are optional. Never activate environments manually; use `uv run`.
The root installs every current member for checks through `--all-packages`.

Use narrow, explained typing exceptions only when third-party or experimental code
requires them. Avoid abstract classes and dependency injection layers with no consumer.
Applications should use structured logs and environment configuration when introduced;
no logging or settings framework is installed for empty packages. Never log secrets.

Keep computational code independent of HTTP handlers and UI. See the
[boundaries](../architecture/boundaries.md) and [local commands](../runbooks/local-development.md).

Ruff selects `E`, `F`, `W`, `I`, `UP`, `B`, `C4`, `T10`, `RUF006` and `RUF100`.
These cover ordinary Python errors/style, imports, modernization, bug patterns,
comprehensions, debugger calls, unreferenced async tasks and unused noqa suppressions.
`E501` is excluded because the formatter handles layout while URLs/strings may stay
long. Docstring, naming and complexity enforcement are not enabled. Only safe lint
fixes run automatically; review hook changes before staging them. The standalone
foundation probe retains its separately scoped configuration.

## Keep fixes small and prevent recurring debt

- Keep progress output outside game/publication error handling. A closed output pipe
  must not turn a saved result into a failed experiment.
- Reserve new backup/export destinations with exclusive creation; checking existence
  first does not prevent another process from creating the file before the write.
- Check completion after the last allowed action. Test both completion at the bound
  and rejection beyond it; do not increase the bound to hide an off-by-one error.
- Add one focused regression for a reproduced bug. Share code only when existing
  consumers need the same behavior; cosmetic shortening does not justify a new layer.
- When a scaffold gains runtime behavior, update its prerequisite and verification
  docs in the same change. Keep planned hosting and measured local behavior distinct.
