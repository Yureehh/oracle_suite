# PKA-001 — simulator compatibility

Evidence date: 2026-10-13. [Reproduction](README.md). Owner review pending.

Pins: Showdown `3a766f2cfb5e51c1e428cfe87d0dba91a8f01640` (0.11.11);
poke-env `7ff6212e4e738efd46f1ea52035b37a8bba1e386` (0.16.1).
Runtime: Node 26.0.0, Python 3.12.13, uv 0.7.5, macOS 26.6.2 arm64 (Apple M2).
The copied upstream npm lock and standalone uv lock resolve dependencies exactly.
Generated JSON includes installed Python distributions and runtime versions.

## Experiments and findings

| Capability | Direct engine | Local server + poke-env | Evidence / limit |
| --- | --- | --- | --- |
| M-C recognition | Supported | Supported | Exact `gen9championsvgc2026regmcbo3`, Champions mod, doubles |
| Supplied teams | Supported | Supported | Both explicit six-member teams validate before engine creation; challenges also use server validator |
| Preview and choices | Supported | Supported | Six visible species, choose four; two active requests; preview 1234 and default actions |
| Champions calculations | Supported for fixture | Unsupported as a complete client representation | Own requested stats are correct; opponent sheet parsing fabricates Generation 9 stats |
| Forced OTS | Supported | Supported | `showteam` packed species/item/ability/moves/nature/gender/level; allocations absent |
| Seed reproducibility | Supported | Unverified through client API | Identical direct seeds produce identical complete logs; client challenge supplies no seed |
| Natural termination | Supported | Supported | Direct fixture finishes in four turns; local games finish without forfeits |
| Bo3 | Unsupported within one Battle | Supported | Engine rule says best-of 3 but one instance ends after one game; server series and client readiness complete three sets |
| Decision snapshot restoration | Supported | Unverified client facility | JSON serialization at first move request reproduces full continuation |
| Independent alternative branch | Supported | Unverified client facility | Switching both leads differs from default continuation; untouched sibling serializes identically |
| Actual-game mechanics parity | Unverified | Unverified | No game capture or controlled console experiment was supplied |

“Supported” is deliberately limited to the measured fixture/protocol case, not every
move, Mega form, targeting choice, switching edge case or timeout. The stream API
is documented to accept teams without validation; the harness uses TeamValidator
first. One invalid duplicate-species fixture is rejected with preserved explanations.
Raw private requests are captured as research evidence, not exported as player observations.

poke-env's OTS handler calls `Pokemon._update_from_teambuilder`, which computes
stats with `GenData.from_gen(9)` and zero allocations when sheets omit them. For
example, opponent Blastoise gets inferred HP 154 although this fixture's Champions
HP is 156. Those client values are neither revealed stats nor justified beliefs.
Own requests subsequently supply authoritative stats. Format string recognition and
successful play therefore do not certify Champions data interpretation.

## Measured timings

A final local run measured engine module load **58.77 ms**, first battle construction
**6.37 ms**, then 100 varied-seed games in **643.36 ms** (median **5.68 ms/game**;
about 155 battles/s for this narrow workload). Validation and battle construction are
included in each warmed sample. JSON transfer and Python subprocess startup are
excluded; runner total wall time is reported separately.

Local server startup to listening measured **6,264.84 ms**. Three client sets took
**11,549.74**, **17,435.46**, and **10,868.56 ms**, completing seven individual games.
The first set includes connection/login initialization; later sets reuse connections.
This path includes server scheduling, websocket messages, client parsing and intergame
readiness. Same supplied teams, preview and default action rule; server-generated
seeds differ and Bo3 may require two or three games. It is not an equal-seed or
per-game speed comparison. Do not extrapolate these simple one-move games to RL.

## Recommendation for PKA-005

Use the pinned direct Node engine for local computation, with mandatory validator
calls and explicit projection of player-visible protocol. Keep set orchestration in
Strixia: fresh engine per game, stable sheets, and separate persistent evidence.
Node serialization gives the needed branching primitive without a custom simulator.
Retain poke-env as an optional protocol/client aid only after a design prevents its
inferred opponent stats and generation-only data from becoming policy facts. No
upstream patch, replacement client or production bridge is implemented here.

No downstream requirement is blocked by these findings, but PKA-005 must explicitly
address client stat interpretation and PKA-008 must implement its own local set lifecycle.
Preparation reported 23 npm dependency advisories (1 low, 5 moderate, 17 high). This
batch did not alter the pin or run an automatic dependency upgrade; public deployment
needs its separately planned dependency/security review.

## Primary sources

- [Pinned simulator API](https://github.com/smogon/pokemon-showdown/blob/3a766f2cfb5e51c1e428cfe87d0dba91a8f01640/sim/SIMULATOR.md).
- [Formats](https://github.com/smogon/pokemon-showdown/blob/3a766f2cfb5e51c1e428cfe87d0dba91a8f01640/config/formats.ts),
  [snapshot implementation](https://github.com/smogon/pokemon-showdown/blob/3a766f2cfb5e51c1e428cfe87d0dba91a8f01640/sim/state.ts),
  [server Bo3](https://github.com/smogon/pokemon-showdown/blob/3a766f2cfb5e51c1e428cfe87d0dba91a8f01640/server/room-battle-bestof.ts).
- [Client OTS/Bo3 handling](https://github.com/hsahovic/poke-env/blob/7ff6212e4e738efd46f1ea52035b37a8bba1e386/src/poke_env/player/player.py),
  [client stat calculation](https://github.com/hsahovic/poke-env/blob/7ff6212e4e738efd46f1ea52035b37a8bba1e386/src/poke_env/battle/pokemon.py).
