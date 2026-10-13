# Strixia worker

This is the reserved entrypoint for computational execution outside API requests.
There is no worker process, queue client or job framework in the scaffold.

A future Python worker should execute real workloads reproducibly, record task states,
handle failure/interruption, and refer to durable artifacts. Domain job logic belongs
in owning libraries; process orchestration and infrastructure adapters belong here.
Core can supply demonstrated lifecycle contracts when Release 0 needs them.

PostgreSQL task claims and local artifact storage are initial candidates, not installed
services. Resource allocation, retries, claim recovery and job semantics remain open
until the first workload. See the [deployment path](../../docs/architecture/deployment.md).
