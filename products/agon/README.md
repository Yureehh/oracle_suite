# Strixia Agon

Agon is Strixia's competitive gaming and game-AI domain: simulation, decision-making,
agent policies, reinforcement learning, strategic evaluation and preparation tools.
The first flagship is [Pokémon VGC](pokemon/README.md). Magic: The Gathering and Poker
remain future possibilities without implementations or package boundaries.

Today only `oracle-arena` is installable, with a Pokémon namespace and smoke tests.
There is no functioning game engine. Reusable code belongs to that Python package;
this directory owns product definitions. Core can supply shared execution and artifact
capabilities when actual consumers justify them. Lyceum will inspect results produced by
Agon rather than create another training system.

Domain-specific mechanics are an established choice. Simulator integration, algorithm
selection and API/UI requirements remain open. Accepted product names reuse
a shared Pokémon evaluator and simulator. Detailed product specifications and verified
workloads are deferred until their requirements are available.
