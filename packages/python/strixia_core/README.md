# Strixia Core

Core 0.3.1 supplies the first demonstrated shared infrastructure: local SQLite run
records and immutable filesystem artifacts. RunStore keeps frozen configurations,
attempt history, fenced game publication, explicit resume, export and backup.
Artifacts publishes without overwriting and verifies byte counts and SHA-256 hashes.
There are no third-party Python runtime dependencies or game-domain imports.

The real consumer is the [local batch coordinator](../../../docs/runbooks/local-batches.md).
This is a concrete local implementation, not a generic persistence/plugin framework.
Database schemas and exports are versioned. Future PostgreSQL/Aurora migration needs
an implementation and migration verification; it is not installed today.

Read the [boundaries](../../../docs/architecture/boundaries.md) and scoped instructions.
