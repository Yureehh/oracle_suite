# Worker rules

Execute computational work outside API handlers. Support reproducible task execution,
meaningful persisted task states when introduced, explicit errors/interruption handling
and relevant execution metadata. Never silently drop tasks.

Keep job logic independent of queue implementation. Account for CPU/GPU resources when
required; prefer idempotent or safely retryable behavior where practical. Define
recovery semantics before implementing durable claims. No queue framework is required
for bootstrap.
