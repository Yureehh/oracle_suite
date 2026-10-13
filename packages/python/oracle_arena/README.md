# Oracle Arena package

Arena owns competitive game AI. The package is currently an installable shell with a
Pokémon namespace and installation/import tests. No game mechanics, environment,
policy, evaluator, trainer or simulator exists yet. There are no runtime dependencies.

Preserve game-specific rules and separate simulation, policies, training and evaluation
as real code arrives. Pokémon VGC is first; Magic and Poker are deferred. Neither a
universal game schema nor a dependency on Core is justified yet.

Read the [Arena definition](../../../products/arena/README.md),
[Pokémon vision](../../../products/arena/pokemon/README.md), and scoped instructions.
Use root [development commands](../../../docs/runbooks/local-development.md).
Simulator choice, representations and learning/search methods remain open until the
Pokémon specification and evidence justify them. Benchmark representative workloads
before performance changes and keep agents independent of presentation.
