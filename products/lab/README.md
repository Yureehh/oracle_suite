# Oracle Lab

Lab is the cross-domain research experience: experiment comparison, training metrics,
model version visibility, benchmarks, evaluation reports and reproducibility information.
It should turn results produced by Arena, Bets and Core into understandable views.

**Current status:** documentation only. There is no Lab backend, experiment tracker,
dashboard or chart data. Core's future run/artifact capabilities may support it, but
Lab must reuse the metadata produced by actual workloads rather than build a second
independent training infrastructure.

Traceable experiment identifiers, configurations, seeds, versions, metrics and provenance
are required for meaningful comparisons. Preserve historical results and distinguish
research runs from production models. See the
[research conventions](../../docs/conventions/ml-research.md).

Open decisions include result contracts, comparison criteria, storage access and UI
requirements. These follow real workload data. Training control, model registry UI,
performance visualizations and cross-domain comparison are deferred; no fabricated
live dashboard or synthetic performance claim belongs here.

## Pokémon research ownership

Pokémon environment, model and training code belongs to Arena. Lab will expose the
actual run metrics, configurations, checkpoint lineage and comparisons produced there,
reusing Core records where justified. The owner is learning RL through small reviewed
tasks; see the [learning path](../../docs/planning/pokemon/learning.md) and
[Lab/League epic](../../docs/planning/pokemon/epics/e08.md). No Lab training backend
or visualization dependency is introduced by this plan.
