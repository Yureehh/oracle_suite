# PKA-038 — model input specification

Schema: `mc-player-v1`. Ruleset: M-C doubles, forced OTS, pinned Showdown
`3a766f2cfb5e51c1e428cfe87d0dba91a8f01640`. This is a local research
representation; it does not establish actual-game parity or a production replay contract.

## Information and chronology

The input contains twelve Pokémon in stable registered order: own six, opponent six.
Opponent stat allocations and exact private HP never enter the representation. OTS
nature is known in this pinned format. Registered and current form, ability and item
remain separate categorical positions. Current ability becomes unknown on public
form change unless permitted evidence supplies it; own request-derived information
can supply the new own ability. Suppression and other announced effects remain
separate from the registered ability.

Each evidence record includes game, turn, increasing sequence, audience, event kind,
complete split protocol payload, numeric/categorical features and contextual feature
tokens. Public payload retains critical-hit, miss, spread/source and order annotations.
Own-state snapshots retain permitted private features. Historical public context excludes own allocations, registered calculated stats and current private PP. Records are bound to their encoding player perspective. The network uses typed features
and context, not arbitrary protocol text. Cosmetic payload text is retained for audit
but is not a language-model input.

Damage evidence includes visible before/after HP fractions, their denominator and
contextual actor/target/field information. No RNG roll or posterior spread is inferred.
Order and base move priority are inputs, not proof of exact effective Speed; modifiers,
priority-changing abilities, Trick Room and ties remain possible explanations.

## Categorical features

Token categorical positions preserve their ordering. IDs use ASCII Showdown normalization.
The vocabulary is sorted and covered by the pinned metadata content identity.

| Family | Source and interpretation |
| --- | --- |
| Species | Registered and currently revealed forms; static base stats/types/weight from Champions Dex |
| Ability/item | Separate registered/current identities from sheets, own information and public reveals; no hidden guesses |
| Nature/status | OTS/own registered nature; current observed status or unknown/absent marker |
| Move/type/category/flags | Known registered moves and pinned move mechanics; candidate move uses the actual request option |
| Target kind | Pinned move target category; explicit selected targets also reference their registered Pokémon |
| Effect | Publicly announced weather, terrain, side or volatile effect identities and emitted sources |

IDs 0/1/2 mean padding/unknown/absent. Numeric states 0/1/2/3 mean
unknown/known/absent/not applicable. Unknown values use zero storage plus their mask,
so an unknown Speed allocation differs from a supplied zero. Padding has its own
token mask. Not-applicable numeric fields are not interpreted as known zero.

## Numeric feature dictionary

The same ordered numeric schema is used for Pokémon, field, event and action tokens.
Fields unused by a token are not applicable. Values are divided by the scale below;
there is no clipping. `hp`/`max_hp` are exact own information only. `hp_precision` is
the observed denominator, not an opponent max-HP estimate. Own fainted max HP can
remain unknown if the current request omits it.

| Fields | Meaning/source |
| --- | --- |
| side, slot, active, selected | Relative side, registered/action position, active position and known selection; opponent unshown reserves stay unknown |
| hp, max_hp, hp_fraction, hp_precision | Current permitted HP and visible fraction/precision |
| level, weight, base_* | Registered level and revealed-form Champions static metadata |
| registered_stat_* | Own native base + points + 75 HP / +20 others, pinned nature flooring; opponent unknown |
| stat_* | Current own request-derived stats; opponent unknown |
| points_* | Own registered native allocations only |
| boost_* | Public stages; in boost events the emitted change/set value; inactive current stages unknown |
| move0_* through move3_* | Known move power/base priority/accuracy and permitted active request PP/disabled flags; nonactive PP unknown |
| turn, game, sequence, event_kind, phase | Chronological and request-phase identifiers |
| pp, disabled, priority, power, accuracy | Current candidate move properties; priority is base move priority, not inferred effective order |
| action_kind, target, mega | Waiting/preview/move/switch/pass code, event target identity and candidate mechanic-use flag |
| effect_count | Announced side-effect layers/presence; no inferred remaining duration |
| before_fraction, after_fraction | Observed damage/healing fractions; random rolls remain latent |
| outcome | Observed prior/current result relative to the player: +1/-1/0 |
| commanding, reviving, force_switch, must_wait, trapped, maybe_trapped, maybe_disabled, maybe_locked, can_mega | Current own request flags, private and contextual; not populated in public history |

Action-kind codes: waiting 0, preview 1, move 2, switch/revival 3, pass 4.
Side is own 0/opponent 1; field effects use -1 for shared battlefield. Pokémon slot
is registered index/5; active is 0 absent, 0.5 first, 1 second. Event actor and target
use (registered index+1)/12, with 0 absent. Preview position is index/3.

| Numeric field | Divisor |
| --- | ---: |
| `side` | 1 |
| `slot` | 1 |
| `active` | 1 |
| `selected` | 1 |
| `hp` | 1000 |
| `max_hp` | 1000 |
| `hp_fraction` | 1 |
| `hp_precision` | 1000 |
| `level` | 100 |
| `weight` | 1000 |
| `turn` | 100 |
| `game` | 3 |
| `sequence` | 1000 |
| `event_kind` | 100 |
| `phase` | 1 |
| `pp` | 64 |
| `disabled` | 1 |
| `priority` | 7 |
| `power` | 250 |
| `accuracy` | 100 |
| `action_kind` | 1 |
| `target` | 1 |
| `mega` | 1 |
| `effect_count` | 6 |
| `outcome` | 1 |
| `commanding` | 1 |
| `reviving` | 1 |
| `force_switch` | 1 |
| `must_wait` | 1 |
| `trapped` | 1 |
| `maybe_trapped` | 1 |
| `maybe_disabled` | 1 |
| `maybe_locked` | 1 |
| `can_mega` | 1 |
| `before_fraction` | 1 |
| `after_fraction` | 1 |
| `move0_power` | 250 |
| `move0_priority` | 7 |
| `move0_accuracy` | 100 |
| `move0_pp` | 64 |
| `move0_disabled` | 1 |
| `move1_power` | 250 |
| `move1_priority` | 7 |
| `move1_accuracy` | 100 |
| `move1_pp` | 64 |
| `move1_disabled` | 1 |
| `move2_power` | 250 |
| `move2_priority` | 7 |
| `move2_accuracy` | 100 |
| `move2_pp` | 64 |
| `move2_disabled` | 1 |
| `move3_power` | 250 |
| `move3_priority` | 7 |
| `move3_accuracy` | 100 |
| `move3_pp` | 64 |
| `move3_disabled` | 1 |
| `registered_stat_hp` | 1000 |
| `registered_stat_atk` | 1000 |
| `registered_stat_def` | 1000 |
| `registered_stat_spa` | 1000 |
| `registered_stat_spd` | 1000 |
| `registered_stat_spe` | 1000 |
| `base_hp` | 255 |
| `base_atk` | 255 |
| `base_def` | 255 |
| `base_spa` | 255 |
| `base_spd` | 255 |
| `base_spe` | 255 |
| `stat_hp` | 1000 |
| `stat_atk` | 1000 |
| `stat_def` | 1000 |
| `stat_spa` | 1000 |
| `stat_spd` | 1000 |
| `stat_spe` | 1000 |
| `points_hp` | 32 |
| `points_atk` | 32 |
| `points_def` | 32 |
| `points_spa` | 32 |
| `points_spd` | 32 |
| `points_spe` | 32 |
| `boost_atk` | 6 |
| `boost_def` | 6 |
| `boost_spa` | 6 |
| `boost_spd` | 6 |
| `boost_spe` | 6 |
| `boost_accuracy` | 6 |
| `boost_evasion` | 6 |

## Protocol coverage and limitations

The reducer handles the following explicitly. State-changing events outside this
register fail with `RepresentationError`; unsupported identities also fail. It does
not silently consult the engine for missing state.

State events: `-ability`, `-boost`, `-clearallboost`, `-clearboost`, `-clearnegativeboost`, `-clearpositiveboost`, `-copyboost`, `-curestatus`, `-cureteam`, `-damage`, `-end`, `-endability`, `-enditem`, `-fieldend`, `-fieldstart`, `-formechange`, `-heal`, `-invertboost`, `-item`, `-mega`, `-setboost`, `-sideend`, `-sidestart`, `-singleturn`, `-start`, `-status`, `-swapboost`, `-transform`, `-unboost`, `-weather`, `detailschange`, `drag`, `faint`, `move`, `replace`, `switch`, `turn`.

Framing/cosmetic events: `-anim`, `-block`, `-center`, `-combine`, `-crit`, `-fail`, `-hint`, `-immune`, `-message`, `-miss`, `-mustrecharge`, `-notarget`, `-nothing`, `-prepare`, `-resisted`, `-supereffective`, `-waiting`, `cant`, `clearpoke`, `gametype`, `gen`, `hint`, `message`, `player`, `poke`, `rated`, `rule`, `showteam`, `start`, `teampreview`, `teamsize`, `tie`, `tier`, `upkeep`, `win`.

Side effects distinguish Spikes/Toxic Spikes layers from single-presence effects.
Single-turn announcements expire at the next turn; effects with public start/end
messages retain those announcements. Remaining duration is unknown.

Transform, added-type effects, single-move effects and `-activate` interactions
are unsupported. Illusion or identities that cannot be uniquely matched to visible
evidence also fail. These are deliberate visible limits, not claims of complete
M-C mechanic coverage. Extend with real fixtures and semantics before training on
a pool that encounters them. Existing action legality remains the separate
[action register](../action-cases.md); representation support does not replace it.

Full raw evidence is preserved, while model features are a selected encoding.
This story implements no spread/range inference, opponent behavior prior,
observation rewind of a live game, Bo3 trainer, search or reward shaping.

Per-player view revisions advance only when that player's permitted content changes;
a sibling-only request refresh cannot change this revision. Own-state records carry
the revision as provenance, never as a neural feature. This distinguishes a newly
revealed trap from an earlier decision with identical public history and turn.

## Verification and decisions

See the [runbook](../../../runbooks/player-models.md) for commands and architecture.
Tests cover hidden-world equivalence, private audiences, chronological cutoffs,
same-game prefix checks, cross-game transient reset, unknown/zero, visible damage,
registered stat rounding, effects, complete paired-menu mapping, terminal/waiting
menus, candidate permutation, padding invariance and synthetic backward passes.
Recorded timing/parameter/memory results are cost evidence only; neither model
has learned to play.
