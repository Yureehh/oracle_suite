# Strixia Agon package

Agon owns competitive game AI. Version 0.3.0 provides a typed Python adapter for
one local Champions M-C game. The [battle guide](../../../docs/planning/pokemon/foundation/005-adapter.md)
explains setup and custom teams. Python has no third-party runtime dependencies;
the adapter requires Node, Git and the built pinned Showdown checkout. Policies,
training, evaluation and Bo3 orchestration remain future work.

Preserve game-specific rules and separate simulation, policies, training and evaluation
as real code arrives. Pokémon VGC is first; Magic and Poker are deferred. Neither a
universal game schema nor a dependency on Core is justified yet.

Read the [Agon definition](../../../products/agon/README.md),
[Pokémon vision](../../../products/agon/pokemon/README.md), and scoped instructions.
Use root [development commands](../../../docs/runbooks/local-development.md).
Simulator choice, representations and learning/search methods remain open until the
Pokémon specification and evidence justify them. Benchmark representative workloads
before performance changes and keep agents independent of presentation.
