# Research reproducibility

No experiment tracker or metadata schema is implemented. The first workload should
record enough evidence to reproduce a run before Lyceum displays it. Keep records with
the producing workload; promote contracts to Core only when justified.

For each experiment capture:

- Run identifier, purpose, timestamps, execution status and failure information.
- Model/checkpoint version, algorithm and complete training/evaluation configuration.
- Game/environment/simulator version and regulation/ruleset.
- Random seeds and deterministic settings, including known nondeterminism.
- Dependency versions, Python version, source commit and dirty-worktree provenance.
- Dataset/team-pool identifiers, source, license and preprocessing/split provenance.
- Training metrics, evaluation results, baseline definitions and uncertainty.
- Artifact locations, content integrity information and resource/hardware context.

Keep training, evaluation, and analysis contexts explicit. Prevent hidden-information
leakage and data leakage across splits. Use time-aware validation for forecasting
where applicable. Preserve historical results and identify research runs separately
from production models. Do not infer optimality from a predicted high value.

Profile a representative workload before optimizing. Record wall time, throughput,
memory, hardware, batch size and CPU/GPU placement as relevant. Measure vectorization,
parallelism, serialization and repeated model loading only once code exists. Store
large data/checkpoints in ignored runtime storage; commit small configs and reports
only when reviewed and free of private data. No fabricated charts or benchmark claims.
