# Architecture overview

Strixia uses one modular repository and will expose its products through one website.
Python owns computation and backend logic. Application entrypoints stay separate
from reusable domain libraries so simulation and research can run without a server.

Core remains an installable shell. Agon 0.3.0 exposes a Python-controlled local
Champions game, using a narrow Node subprocess for pinned Showdown. Neither package
has Python runtime dependencies or a dependency on the other. API, web, and worker directories
contain documentation only. Products document intended outcomes, not implementations.

Agon owns game AI; Pokémon VGC is first. The separate Oracle Bets project is the future Pythia integration source
and is not a workspace member. Lyceum will read actual experiment results from workloads.
Core will acquire shared capabilities only for demonstrated use cases. Theoria,
Delphi, Metis and Techne are accepted product names sharing a Pokémon engine.

Per [ADR 0002](../decisions/0002-pokemon-discovery-and-planning.md), a bounded Champions
simulator compatibility study comes first. The subsequent Release 0 slice should
define a durable execution lifecycle with one API,
one Python worker, metadata, and artifacts; then connect one genuine Agon workload.
PostgreSQL task claims and filesystem artifact storage are candidates, not installed
components. No queue broker, auth framework, service-per-product architecture or
universal game interface is needed for this scaffold.

Read [boundaries](boundaries.md), [deployment](deployment.md), and the
[initial ADR](../decisions/0001-monorepo-architecture.md). Product specifications live
under `products/` and remain the authoritative domain documents.
