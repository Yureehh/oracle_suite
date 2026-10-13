# Infrastructure

No infrastructure is provisioned. This directory will hold reviewed deployment and
local-service configuration only when real applications require it. The scaffold
needs no containers, databases, queues, hosting account or GPU.

Read the [deployment path](../docs/architecture/deployment.md) before introducing
services. PostgreSQL and local artifacts are candidates for Release 0; containers
and object storage remain future options. Record prerequisites, migrations, backup
and restore behavior, secret handling and teardown with each actual configuration.
