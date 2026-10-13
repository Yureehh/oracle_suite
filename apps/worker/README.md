# Strixia local worker

`local.py` is the runnable Python coordinator for one durable batch of independent
Champions games. It uses Core's SQLite records and immutable artifacts, and Agon's
pinned engine adapter. A bounded thread pool drives independent Node processes;
training and policies remain Python. No queue broker or web framework is required.

Read the [batch runbook](../../docs/runbooks/local-batches.md) for submission,
execution, status, explicit resume, cancellation and export commands. Supported
platforms are local macOS/Linux. There is no multi-host scheduling, cloud failover,
mid-turn recovery, Bo3 runner or trainer in this implementation.
