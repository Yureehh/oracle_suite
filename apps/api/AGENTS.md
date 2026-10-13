# API rules

Prefer FastAPI when implementation begins. Use typed request/response schemas, validate
external inputs, keep handlers thin and provide clear error semantics. Delegate heavy
work to asynchronous execution/workers.

Separate API schemas from domain/persistence models when justified. Prepare actual
services for authentication/authorization without inventing an auth platform. Do not
introduce routes merely to make the scaffold look executable.
