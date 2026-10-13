# Architecture overview

Strixia uses one modular repository and will expose its products through one website.
Python owns computation and backend logic. Application entrypoints stay separate
from reusable domain libraries so simulation and research can run without a server.

Core 0.3.0 supplies concrete local SQLite run records and immutable artifacts.
Agon 0.4.0 supplies a Python-controlled Champions game and paired action menus,
using a narrow Node subprocess for pinned Showdown. Neither package has third-party
Python runtime dependencies or a dependency on the other. A local worker imports
both; API and web directories contain documentation only. Products document intended outcomes, not implementations.

Agon owns game AI; Pokémon VGC is first. The separate Oracle Bets project is the future Pythia integration source
and is not a workspace member. Lyceum will read actual experiment results from workloads.
Core will acquire shared capabilities only for demonstrated use cases. Theoria,
Delphi, Metis and Techne are accepted product names sharing a Pokémon engine.

Per [ADR 0002](../decisions/0002-pokemon-discovery-and-planning.md), a bounded Champions
simulator compatibility study came first. A local worker now persists independent
Agon games; API integration and genuine Bo3 workloads remain later Release 0 steps.
SQLite records and filesystem artifacts now serve the local batch worker. PostgreSQL
and shared storage remain future candidates. No queue broker, auth framework, service-per-product architecture or
universal game interface is needed for this scaffold.

Read [boundaries](boundaries.md), [deployment](deployment.md), and the
[initial ADR](../decisions/0001-monorepo-architecture.md). Product specifications live
under `products/` and remain the authoritative domain documents.
