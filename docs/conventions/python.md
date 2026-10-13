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
