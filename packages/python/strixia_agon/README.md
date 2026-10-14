# Strixia Agon package

Agon owns competitive game AI. Version 0.5.0 provides a typed Python adapter, complete
paired action menus and a seeded uniform random policy for Champions M-C games.
The [battle guide](../../../docs/planning/pokemon/foundation/005-adapter.md)
explains setup and custom teams. Python has no third-party runtime dependencies;
the adapter requires Node, Git and the built pinned Showdown checkout. Policies,
training and model evaluation remain future work. The [local batch worker](../../../docs/runbooks/local-batches.md)
executes and records bounded Bo3 sets, using Agon's pinned series scoring.

Preserve game-specific rules and separate simulation, policies, training and evaluation
as real code arrives. Pokémon VGC is first; Magic and Poker are deferred. Neither a
universal game schema nor a dependency on Core is justified yet.

Read the [Agon definition](../../../products/agon/README.md),
[Pokémon vision](../../../products/agon/pokemon/README.md), and scoped instructions.
Use root [development commands](../../../docs/runbooks/local-development.md).
The direct engine integration is selected; representations and learning/search
methods remain research choices. Benchmark representative workloads
before performance changes and keep agents independent of presentation.

Player-visible choices live in `strixia_agon.pokemon.actions`. See the evolving
[action register](../../../docs/planning/pokemon/action-cases.md). Known-invalid
pairs are excluded; protocol-permitted request updates preserve newly revealed
restrictions. No greedy pair pruning or live hidden-state legality oracle is used.

`strixia_agon.pokemon.matches` supplies `RandomPolicy.choose(view)`, `play_game` and
`series_result`. A policy receives only its own player view. Each game derives
separate policy seeds for each player, independent of scheduling; the engine still
owns chance. Public prior-game history is retained as dated evidence, without spread
inference or strategic adaptation. This baseline tests execution, not strength.
