# PKA-002 — Champions rules and legality

Evidence date: 2026-10-13. M-C doubles, Bo3, OTS; [reproduction](README.md).
The same [pinned versions](001-simulator.md) apply. Owner accepted on 2026-10-13;
review was pending at the original handoff.
No in-game controlled experiment was run. “Engine” below means the inspected pin,
not an official guarantee. Missing official details stay unverified.

## Dated evidence table

| Subject | Official evidence inspected | Pinned engine / measured result | Status or discrepancy |
| --- | --- | --- | --- |
| M-C period | [M-C notice](https://champions-news.pokemon-home.com/en/page/816.html): 9 September–2 December 2026 UTC | Selected exact M-C format, never current defaults | Official period; format parity otherwise unverified |
| Allocations | [Training page](https://champions.pokemon.com/en-us/pokemon/) permits adjusting stats; no numeric cap stated | Validator caps each stat at 32, total at 66; lower bound zero | Numeric rules independently unverified in game/official text |
| Calculation | No formula on inspected official pages | HP = base HP + points + 75; other stats = base + points + 20 before nature | Engine-backed only |
| Nature rounding | No numeric nature rule on inspected pages | Floor multiplied stat by 110/100 or 90/100; engine also truncates intermediate product to 16 bits | Hand examples match; game rounding unverified |
| Level | Inspected M-C notice does not specify level behavior | Input levels 1, 50, 100 normalize to 50; 101 rejected | Selected engine uses Adjust Level 50, not level-dependent Champions custom rules |
| IV representation | No IV training promise in inspected official text | All engine IV fields must equal 31; nonmax value rejected; fixed-level formula ignores them | Internal compatibility field, never a user training dimension |
| Species | Official notice links a dynamic [eligible roster](https://web-view.app.pokemonchampions.jp/battle/pages/events/rs178713870219xeaaio/en/pokemon.html) | Champions formats-data/Obtainable/Flat Rules; fixture species validate, Mew rejected | Dynamic official roster text was not extractable; full roster parity unverified |
| Held items | Official notice forbids duplicate held items and describes eligible Mega Stones | Champions items + Item Clause 1; duplicate Sitrus Berry and unavailable Ability Shield rejected | Clause agrees; complete item availability unverified |
| Moves | Training page permits changing moves and warns unusable visiting moves need replacement | Champions learnsets/moves; Greninja Spore rejected | Fixture legality established; full move/mechanics parity unverified |
| Abilities | Training page permits changing abilities | Champions abilities; Greninja Wonder Guard rejected | Fixture legality established; full ability/mechanics parity unverified |
| Team composition | Inspected M-C notice does not give roster/selection size | Exactly six registered, select four, two active; four/seven registered rejected | Project chooses six-member VGC fixtures; do not claim official ranked roster minimum |
| Mega Evolution | Official notice permits one Mega Evolution per battle with a suitable stone | Champions action scripts implement Mega eligibility; no Mega used by fixtures | Official rule; new-form mechanics unverified by this batch |
| Timers | Official notice: total 20 min, player 7 min, turn 45 sec, preview 90 sec | Format inherits VGC Timer; benchmark defaults complete without timeout | Official timer values; server timer parity not experimentally established |
| Bo3 / OTS | Chosen research scope; inspected ranked notice does not establish event Bo3/OTS | Bo3 format forces OTS; server handles series; nature exposed, allocations omitted | Project requirement, not a claim that ranked mode is universally Bo3/OTS |

## Allocation experiments

`002.json` preserves submitted and normalized teams plus **unaltered engine rejection
strings**. Boundary inputs were derived from validator and rule-table source before
construction. No conversion of old EVs was used.

| Case | Observed validator result |
| --- | --- |
| All zero, Hardy neutral nature | Accepted |
| All zero, Serious neutral nature | Rejected as probable missing investment, an engine import warning |
| HP 32 / Atk 32 / Spe 2, total 66 | Accepted |
| HP 33 | Rejected: more than 32 Stat Points |
| HP −1 | Rejected; error incorrectly calls them “Awakening Values” |
| HP 0.5 | **Accepted unchanged: validator gap** |
| HP 32 / Atk 32 / Spe 3, total 67 | Rejected: total exceeds 66 |
| Speed IV 0 | Rejected: this engine format requires IVs 31 |

Do not silently convert the fractional case into a passing integer-validation claim.
The future Strixia input boundary should reject non-integer points before invoking
the engine. That is a proposed PKA-005/021 requirement, not an implemented public
schema or independently official game fact. The Serious warning should similarly
not be advertised as game illegality; intentional zero investment has a neutral
Hardy representation accepted by this engine. No upstream fixes were made.

## Hand calculations

Greninja's inspected base stats are HP 72 / Atk 95 / Def 67 / SpA 103 / SpD 71 /
Spe 122. Fixture points are HP 2 / Atk 32 / Spe 32, zero elsewhere.

| Nature | HP | Atk | Def | SpA | SpD | Spe |
| --- | --- | --- | --- | --- | --- | --- |
| Hardy | 149 | 147 | 87 | 123 | 91 | 174 |
| Timid | 149 | 132 | 87 | 123 | 91 | 191 |
| Modest | 149 | 132 | 87 | 135 | 91 | 174 |

For Timid Speed, floor(174 × 110 / 100) = 191; reduced Attack is
floor(147 × 90 / 100) = 132. Modest SpA is floor(123 × 110 / 100) = 135.
All six values match engine outputs for all three examples. HP does not take a
nature multiplier. These examples cover normal fixture stats, not extreme hacked
16-bit overflow cases. Level Clause Mod exists upstream but is absent from M-C;
its historical-style level-dependent branch must not be used for this scope.

## Proposed future input mapping

Expose six **stat points**, nature, species, legal moves, ability and item. Copy
native integer point values directly into the engine's historical `evs` keys
`hp/atk/def/spa/spd/spe`. Supply all-six `ivs=31` only as an engine sentinel and let
M-C adjust level to 50. No IV optimization, EV scaling, transfer conversion, or
legacy importer is implied. Validate integer shape and native limits at the Strixia
boundary, then validate the complete team in the pinned format. Availability cannot
be determined by the ordinary Generation 9 dex alone.

Review findings affecting downstream work: fractional-input guard; zero-investment
warning mapping; official numeric/stat/roster parity remains open. They do not stop
research projection work in PKA-003. Game verification must precede claims of game
accuracy; no automatic adoption of third-party planner mechanics.

## Inspected pinned source

All links use the same engine commit:
[stat calculation](https://github.com/smogon/pokemon-showdown/blob/3a766f2cfb5e51c1e428cfe87d0dba91a8f01640/data/mods/champions/scripts.ts),
[validation](https://github.com/smogon/pokemon-showdown/blob/3a766f2cfb5e51c1e428cfe87d0dba91a8f01640/sim/team-validator.ts),
[66-point limit and selection size](https://github.com/smogon/pokemon-showdown/blob/3a766f2cfb5e51c1e428cfe87d0dba91a8f01640/sim/dex-formats.ts),
[Champions rules](https://github.com/smogon/pokemon-showdown/blob/3a766f2cfb5e51c1e428cfe87d0dba91a8f01640/data/mods/champions/rulesets.ts),
[species availability](https://github.com/smogon/pokemon-showdown/blob/3a766f2cfb5e51c1e428cfe87d0dba91a8f01640/data/mods/champions/formats-data.ts),
[items](https://github.com/smogon/pokemon-showdown/blob/3a766f2cfb5e51c1e428cfe87d0dba91a8f01640/data/mods/champions/items.ts),
[learnsets](https://github.com/smogon/pokemon-showdown/blob/3a766f2cfb5e51c1e428cfe87d0dba91a8f01640/data/mods/champions/learnsets.ts),
[moves](https://github.com/smogon/pokemon-showdown/blob/3a766f2cfb5e51c1e428cfe87d0dba91a8f01640/data/mods/champions/moves.ts),
[abilities](https://github.com/smogon/pokemon-showdown/blob/3a766f2cfb5e51c1e428cfe87d0dba91a8f01640/data/mods/champions/abilities.ts).
