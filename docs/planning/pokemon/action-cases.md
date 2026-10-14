# Champions action edge cases

Living register for PKA-006, audited 2026-10-13 against Showdown
`3a766f2cfb5e51c1e428cfe87d0dba91a8f01640`. Only M-C doubles is enabled.
“Engine tested” means a controlled pinned-engine fixture; “projection tested” means
an explicitly constructed player request. Neither establishes independent actual-game
fidelity. This is a maintained coverage register, not a claim that every battle
combination has been tested.

Source anchors: [choice validation](https://github.com/smogon/pokemon-showdown/blob/3a766f2cfb5e51c1e428cfe87d0dba91a8f01640/sim/side.ts),
[target geometry](https://github.com/smogon/pokemon-showdown/blob/3a766f2cfb5e51c1e428cfe87d0dba91a8f01640/sim/battle.ts),
[player requests](https://github.com/smogon/pokemon-showdown/blob/3a766f2cfb5e51c1e428cfe87d0dba91a8f01640/sim/pokemon.ts),
[Champions overrides](https://github.com/smogon/pokemon-showdown/blob/3a766f2cfb5e51c1e428cfe87d0dba91a8f01640/data/mods/champions/scripts.ts).

| Case | M-C handling and evidence | Future recheck |
| --- | --- | --- |
| Preview: select four of six, ordered leads/reserves | 360 complete ordered choices; engine-tested progression | Selection sizes, positional symmetry and format restrictions |
| Duplicate reserve switch | Excluded from paired menu; engine rejects duplicate switch-in | Slot/replacement rules |
| Already active or fainted reserve | Excluded from normal switches | Special revival and format rules |
| Both actives faint with one reserve | Both permitted switch/pass assignments; engine tested | Forced pass counts and replacement timing |
| Waiting player / completed battle | One None choice / empty menu | Protocol phase changes |
| Regular targets including ally | Engine-tested normal, ally and spread examples; Python mirrors doubles geometry | Every new target type, new formats/slot counts |
| Self, ally-or-self, adjacent foe, automatic/random/scripted targets | Explicit target mapping; unknown targets fail visibly | Add fixture evidence as encountered; never silently guess |
| Disabled moves | Exclude known-disabled request moves | Taunt, Encore, Torment, Disable, choice items, Assault Vest, Imprison and ability interactions |
| Locked moves and exhausted PP / Struggle | Locked requests may omit PP; synthetic Struggle tested | Recharge/two-turn move requests, partially hidden locks |
| Hidden trapping | Keep uncertain switches selectable; real Mega Gengar Shadow Tag rejection updates own request | Shadow Tag, Arena Trap, Magnet Pull, typing/item/ability exemptions |
| Perish Song plus trapping | Track legality separately from survival strategy; full scenario fixture remains future coverage | Legal species/moves and escape rules in each regulation |
| A submission reveals disabled/locked/trapped information | Preserve only protocol-emitted private request changes; roll back queued choices/history/turn/RNG. Consecutive bilateral trap refreshes retain each player's earlier reveal | Real Imprison and single/bilateral Mega Gengar trapping are engine tested; locked-move combinations remain future coverage |
| Commander | Commanding slot passes; projection tested | Real Dondozo/Tatsugiri interaction and eligibility |
| Revival Blessing | Legal Pawmot fixture: choose fainted ally, reject healthy target; engine tested | Revival plus simultaneous replacement / multiple revivals |
| Duplicate Mega / Mega X/Y | Shared usage filtered and engine tested with Charizardite X/Y; these stones use ordinary mega command in M-C | New stones/forms and request flags; separate megax/megay flags if actually exposed |
| Duplicate Z-Move | Pinned engine has shared Z-use check; all eligible Z items are absent from the pinned Champions Dex; not exposed by M-C adapter | Revalidate all legal crystals and per-move Z requests before another format |
| Duplicate Dynamax / Max Moves | Pinned engine checks generation, shared use and existing Dynamax; unsupported M-C request flags fail explicitly | Available generations/formats, transformed move targets, Max Guard |
| Duplicate Terastallization | Pinned engine checks shared use; Champions action override returns null | Future Champions eligibility, type fields and shared resource |
| Ultra Burst / combinations of mechanics | Pinned engine has separate usage flags; not enabled in M-C adapter | Do not assume different mechanics share a resource; inspect actual format |
| Misses, Protect, immunity, redirection, priority/speed order | Remain legal strategic risks, resolved by the engine | Legal target versus resolution behavior; no hindsight filtering |
| Stale or wrong-player choices | JointChoice binds to immutable player view; rejected before submission | Repeated request boundaries and future observations |
| Hidden worlds, identical visible history | Identical menus in hidden-spread/seed fixture | New observations or request fields must pass equivalence checks |

Live policies receive their own menu/view. Offline tests may ask the engine whether
candidates are accepted, but a live omniscient accept/reject oracle would leak hidden
information. Controller errors and both private views belong to trusted orchestration;
route newly revealed information only to the appropriate player.

## Gate for every future regulation

[PKA-062](epics/e12.md#pka-062) requires pinned source/rule/validator rechecks before
enabling another Champions format. Inspect legal species, items, moves, abilities,
native points, preview and OTS; revisit every row above, including previously absent
mechanics. Validate new fixtures and request schemas, update tested/untested status,
rerun hidden-world and joint-choice acceptance checks, and record the evidence.
Unsupported flags are explicit errors until verified support is implemented.
