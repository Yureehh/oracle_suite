# Pokémon product and research rules

Prioritize VGC Best-of-3 Open Team Sheets initially. Develop against versioned,
externally validated rules and record regulation/environment versions with experiments.
Preserve player information boundaries; policies must not receive hidden opponent
information accidentally. Distinguish playing, training and analysis contexts and
model simultaneous decisions explicitly when relevant.

Algorithms, model architectures, representations and search methods are research
choices requiring evidence. A high predicted value does not establish optimal strategy.
Report evaluation metrics, uncertainty and provenance; keep analysis/training reproducible.

Theoria, Delphi, Metis and Techne are accepted branding, never automatic service
boundaries. Reuse Pokémon simulation/evaluation across products. Respect platform rules
and competitive fair-play constraints for automated play. Read this directory’s README for agreed requirements and `docs/planning/pokemon/`
for the current board, story and research gates. Do not invent unapproved mechanics.

## Collaborative work and learning

Models target Champions regulations only; initially M-C Bo3 OTS. Validate native stat
allocations; do not apply historical EV/IV formulas or assume all Gen 9 client data is
Champions-compatible. Explain RL/search concepts before implementation; the owner is
learning. Search is optional and double-oracle action expansion is distinct from depth.

Read `docs/planning/pokemon/README.md` and the authoritative board before proposing work.
Every implementation needs a scoped design and explicit owner approval. Complete one
approved task, record actual verification, move it to In Review and wait. Only owner
acceptance permits Done. Do not automatically start another task. Board approval is
not approval to code, commit, push, spend or deploy. Use the documented main/dev/task
branch workflow once Git setup is separately authorized.

Keep training, policies, models, evaluation and set orchestration in Python. Limit
JavaScript to the upstream Showdown engine boundary. Decide hosting and transport
optimizations from measured workloads rather than speculative infrastructure.

Pokémon training code belongs in Agon; Lyceum views existing run/model records. Keep
neutral/learned beliefs explicit, preserve chronological set evidence and state-fidelity
limits. Missing-spread replay imports stay viewer-only; supplied spreads alone never
prove exact counterfactual reconstruction. Optimize measured quality per cost, never
correctness away. Trainer/model/search choices stay hypotheses until tested and approved.
