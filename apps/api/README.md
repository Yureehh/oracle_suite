# Oracle API

This directory is reserved for the future backend entrypoint. It contains documentation
only; there is no FastAPI application, server command or API dependency yet.

FastAPI is the current preference when requirements arrive. Handlers should validate
typed requests, orchestrate domain use cases and return clear error semantics. Keep
business/computational logic in packages. Delegate expensive jobs to workers.

Core may supply actual execution contracts later; it must not depend on this app.
Request/response contracts, authentication and persistence remain open. The Release 0
slice will define a minimal API alongside durable execution. See the
[deployment direction](../../docs/architecture/deployment.md). No speculative auth
platform or endpoint set is implemented now.
