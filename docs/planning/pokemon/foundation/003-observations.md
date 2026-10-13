# PKA-003 — player observations and Bo3 knowledge

Evidence date: 2026-10-13. M-C doubles, Bo3, OTS; [reproduction](README.md).
Owner review pending. This is a research specification with projection examples,
not a stable public library, observation tensor or production protocol parser.

## Information categories

| Category | Contents | Use |
| --- | --- | --- |
| Omniscient simulator state | Both allocations/stats, teams and chosen reserves, private requests, queued choices, RNG, effects and internal caches | Engine execution and privileged research checks only; never policy input |
| Public evidence | Preview roster/details, OTS, publicly resolved moves/switches/damage/status/field changes and outcome | Shared history known equally to both players |
| Own private information | Own complete team/spread, exact own HP/stats, available actions and replacements | This player's view only; derive useful fields from their request, do not copy raw requests |
| Hypothetical beliefs | Optional neutral scenarios, inferred ranges or learned/metagame priors | Explicit assumptions with source/time/confidence, separate from known facts |
| Persistent set knowledge | Chronological public and permitted own-private evidence from earlier games | May constrain later scenarios; never retroactively alter earlier observations |

An information set groups different hidden worlds that look the same to a player.
The player must receive the same observation in each such world. Hidden actual
allocations can change damage later, but cannot be exposed before evidence reveals
them. A precise engine value is not automatically something the player knows.

## Visibility by phase

| Phase | Shared visibility | Player's private visibility | Excluded |
| --- | --- | --- | --- |
| Preview | Six roster entries and forced OTS for both teams | Own allocations/stats and preview options | Opponent allocations/stats, their selected four/order, raw requests, RNG |
| Before simultaneous choices | Prior resolved history, active Pokémon and public battle conditions | Own exact HP/stats and legal options; own selection is personally known | Opponent choice, their unshown reserves, every submitted choice payload, internal queue and RNG |
| After resolution | Public move order, switches, visible damage/HP fractions, status, effects, outcomes | Own exact HP changes and request-derived options | Opponent exact HP/max HP and true spread unless legitimately disclosed independently |
| Between games | Dated accumulated evidence, unchanged sheets and game outcomes | Own fixed team knowledge | Old active positions/HP/status/PP/field conditions/requests as current battle state |

Freeze the decision observation before either submitted choice becomes available
through omniscient state. A waiting request or a sibling's queued action cannot
update that observation. All six OTS entries are visible, but the unshown members
of the opponent's selected four are still hidden until their participation is revealed.
The fact that they selected a Pokémon in G1 does not reveal their G2/G3 selection.

## Protocol-derived OTS and privacy

At the pinned format's preview, `|showteam|p1|...` and `|showteam|p2|...` expose packed
species, held item, ability, moves, **nature**, gender and level. Empty items are
valid visible values. Stat points and IVs are omitted. Nature is therefore known
in this Champions format, even when allocations are not. See
[Battle.showOpenTeamSheets](https://github.com/smogon/pokemon-showdown/blob/3a766f2cfb5e51c1e428cfe87d0dba91a8f01640/sim/battle.ts)
and the [forced OTS rule](https://github.com/smogon/pokemon-showdown/blob/3a766f2cfb5e51c1e428cfe87d0dba91a8f01640/data/rulesets.ts).
Do not import unrelated Generation 9 Tera visibility as a Champions requirement.

The engine log has `|split|pN` blocks containing a private line followed by a public
line. Public damage in the fixture includes `36/100`; the owning player sees exact
HP. The harness calls pinned `extractChannelMessages` for channel 0 (shared), 1
(p1) and 2 (p2), rather than stripping split markers itself. Raw `sideupdate` requests
are private, and `end` data is privileged. Upstream
[getPlayerStreams](https://github.com/smogon/pokemon-showdown/blob/3a766f2cfb5e51c1e428cfe87d0dba91a8f01640/sim/battle-stream.ts)
already separates those channels and discards the privileged end block from players.
Future PKA-005 should reuse this boundary and still explicitly project policy fields.

poke-env's populated opponent stats from OTS are **unsupported guesses**, not known
information. The examples retain engine-requested own stats but permit only the
actual sheet fields for opponents. Raw requests, snapshots and traces remain in
ignored research storage. Own legal options are useful information; a raw private
request object is not an observation contract.

## Chronological ledger and set reset

Each evidence record has a unique increasing sequence, game number, turn, event
kind, audience, immutable payload and provenance. Event kinds identify preview
sheets, before-choice own information, resolution damage/order/reveals and outcomes;
sequence orders events within a turn. A future production ledger must retain an
explicit decision/phase identifier as well. Reconstruction takes a player, current
game and sequence cutoff. Later entries cannot enter earlier views.

Persist sheets, reveals and relevant damage/order evidence with their original
context. Own private evidence stays private across the set. Reset current HP,
status, boosts, weather/terrain/field effects, active slots, PP and private requests
when the new game starts. Never treat earlier damage as current HP. Repeated OTS
should agree within the chosen fixed-team set; changed sheets require an explicit
set-integrity decision in PKA-008, not silent merging.

Separate three things in explanations:

- Observed fact: a public HP fraction or move order at a particular turn.
- Inferred range: a constraint derived under specified mechanics and assumptions.
- Optional prior: how scenarios are weighted before enough evidence exists.

Damage fractions have rounding uncertainty. Spread move modifiers, critical hits,
abilities, items, field effects and RNG rolls affect interpretation. Order alone does
not prove exact Speed: priority, speed modifiers, Trick Room and ties matter.
A damage roll is latent; the observed HP change is evidence about possible rolls,
not knowledge of the sampled RNG state. This batch computes no posterior, range,
learned prior or likelihood.

A truthful G1 explanation is “Opponent nature is known from OTS; allocation is still
unknown.” A later explanation may say “We observed these damage fractions in G1
and G3; they can constrain compatible allocations once the inference module accounts
for these contexts.” Numeric ranges must wait for PKA-024's verified calculation.

## Demonstrated examples and tests

Two engine-valid worlds keep gender/roster/sheets constant and differ in Blastoise's
hidden allocation, RNG seed, opponent private request and submitted action. Gender
is held at M in these visibility variants because seed-driven random gender would
otherwise make the worlds visibly different. At preview and the first move boundary,
p1's actual protocol history and own request are identical; projected observations
are identical. This covers a real information boundary, not just a fake dictionary.

The baseline game then resolves normally. Public and owning-player damage channels
differ as expected. To demonstrate chronology, the example **synthetically labels
captured G1 damage/order as later G3 evidence**. It is not an additional measured
three-game set or evidence that a numeric spread was inferred. The G3 projection
has more evidence and no stale G1 private battle state. Reconstructing G1 with its
saved cutoff yields exactly the saved G1 observation.

Nine leakage tests cover hidden-world equivalence, public versus private HP,
future evidence, malicious extra hidden fields, private beliefs versus facts,
wrong-player requests, invalid chronology sheet-field whitelisting and symmetric own-team privacy. Together
with PKA-001/002 there are fifteen standalone tests. Hypothetical ranges in the
privacy test are explicitly illustrative and uncomputed.

Limits: research entries trust provenance supplied by the harness; arbitrary raw
protocol or user-supplied records need a production parser and boundary validation.
The examples do not reconstruct every volatile state, target mask or mechanic.
PKA-005/006/008/023 must design those contracts before implementation. Nothing here
permits a policy to consume raw engine state or future revelations.
