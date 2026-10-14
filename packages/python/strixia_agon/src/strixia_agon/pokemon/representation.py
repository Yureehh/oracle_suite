"""Player-only structured evidence and full-history model inputs (schema 1)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field

from .actions import JointChoice, choices
from .mechanics import Mechanics, identifier
from .simulator import PlayerView, TeamMember

SCHEMA = "mc-player-v1"
# Values always travel with a state: unknown, known, absent, not applicable.
UNKNOWN, KNOWN, ABSENT, NA = range(4)
STATS = ("hp", "atk", "def", "spa", "spd", "spe")
BOOSTS = ("atk", "def", "spa", "spd", "spe", "accuracy", "evasion")
NUMERIC_FIELDS = (
    "side",
    "slot",
    "active",
    "selected",
    "hp",
    "max_hp",
    "hp_fraction",
    "hp_precision",
    "level",
    "weight",
    "turn",
    "game",
    "sequence",
    "event_kind",
    "phase",
    "pp",
    "disabled",
    "priority",
    "power",
    "accuracy",
    "action_kind",
    "target",
    "mega",
    "effect_count",
    "before_fraction",
    "after_fraction",
    *(f"move{i}_{k}" for i in range(4) for k in ("power", "priority", "accuracy")),
    *(f"registered_stat_{s}" for s in STATS),
    *(f"base_{s}" for s in STATS),
    *(f"stat_{s}" for s in STATS),
    *(f"points_{s}" for s in STATS),
    *(f"boost_{s}" for s in BOOSTS),
)
SCALES = dict.fromkeys(NUMERIC_FIELDS, 1.0) | {
    "hp": 1000.0,
    "max_hp": 1000.0,
    "hp_precision": 1000.0,
    "level": 100.0,
    "weight": 1000.0,
    "turn": 100.0,
    "game": 3.0,
    "sequence": 1000.0,
    "event_kind": 100.0,
    "pp": 64.0,
    "priority": 7.0,
    "power": 250.0,
    "accuracy": 100.0,
    "effect_count": 6.0,
    **{
        f"move{i}_{k}": v
        for i in range(4)
        for k, v in (("power", 250.0), ("priority", 7.0), ("accuracy", 100.0))
    },
    **{f"registered_stat_{s}": 1000.0 for s in STATS},
    **{f"base_{s}": 255.0 for s in STATS},
    **{f"stat_{s}": 1000.0 for s in STATS},
    **{f"points_{s}": 32.0 for s in STATS},
    **{f"boost_{s}": 6.0 for s in BOOSTS},
}
PHASES = ("teampreview", "move", "switch", "end")
# Cosmetic/framing messages do not change battle state. They remain in history.
COSMETIC = frozenset(
    (
        "",
        "gametype",
        "player",
        "gen",
        "tier",
        "rule",
        "clearpoke",
        "poke",
        "teampreview",
        "showteam",
        "teamsize",
        "start",
        "upkeep",
        "win",
        "tie",
        "rated",
        "-supereffective",
        "-resisted",
        "-crit",
        "-miss",
        "-fail",
        "-immune",
        "-notarget",
        "-activate",
        "-block",
        "cant",
        "-hint",
        "hint",
        "message",
        "-message",
        "-anim",
        "-prepare",
        "-mustrecharge",
        "-waiting",
        "-combine",
        "-nothing",
        "-center",
    )
)
STATE_EVENTS = frozenset(
    (
        "turn",
        "switch",
        "drag",
        "replace",
        "move",
        "faint",
        "-damage",
        "-heal",
        "-status",
        "-curestatus",
        "-cureteam",
        "-boost",
        "-unboost",
        "-setboost",
        "-clearboost",
        "-clearallboost",
        "-clearnegativeboost",
        "-clearpositiveboost",
        "-invertboost",
        "-copyboost",
        "-swapboost",
        "-weather",
        "-fieldstart",
        "-fieldend",
        "-sidestart",
        "-sideend",
        "-start",
        "-end",
        "-singleturn",
        "-singlemove",
        "-item",
        "-enditem",
        "-ability",
        "-endability",
        "detailschange",
        "-formechange",
        "-mega",
        "-transform",
    )
)
EVENT_KINDS = tuple(sorted(COSMETIC | STATE_EVENTS | {"own-state"}))


class RepresentationError(ValueError):
    """Evidence cannot be faithfully represented by this schema."""


@dataclass(frozen=True)
class Features:
    categories: tuple[int, ...]
    values: tuple[float, ...]
    states: tuple[int, ...]


def features(
    m: Mechanics,
    categories: Sequence[tuple[str, str | None]] = (),
    **numbers: float | None,
) -> Features:
    unknown = set(numbers) - set(NUMERIC_FIELDS)
    if unknown:
        raise RepresentationError(f"Unknown numeric fields {unknown}")
    return Features(
        tuple(m.category(k, v) for k, v in categories),
        tuple(float(numbers.get(k) or 0.0) / SCALES[k] for k in NUMERIC_FIELDS),
        tuple(
            NA if k not in numbers else UNKNOWN if numbers[k] is None else KNOWN
            for k in NUMERIC_FIELDS
        ),
    )


@dataclass(frozen=True)
class Evidence:
    game: int
    turn: int
    sequence: int
    audience: str
    kind: str
    payload: tuple[str, ...]
    features: Features
    context: tuple[Features, ...]


@dataclass(frozen=True)
class EvidenceContext:
    """Completed earlier-game evidence; audience and cutoff are checked on encode."""

    records: tuple[Evidence, ...] = ()
    game: int = 1
    cutoff: int | None = None


@dataclass(frozen=True)
class Candidate:
    choice: JointChoice
    parts: tuple[Features, ...]
    references: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class Observation:
    schema: str
    mechanics_id: str
    player: str
    game: int
    turn: int
    pokemon: tuple[Features, ...]
    field: tuple[Features, ...]
    history: tuple[Evidence, ...]
    candidates: tuple[Candidate, ...]


@dataclass
class _Mon:
    species: str
    ability: str
    item: str
    nature: str
    moves: tuple[str, ...]
    level: int
    current_species: str = ""
    current_ability: str | None = None
    current_item: str | None = None
    status: str | None = None
    hp: float | None = None
    maximum: float | None = None
    exact: bool = False
    active: int = -1
    selected: bool | None = None
    boosts: dict[str, int] = field(default_factory=dict)
    effects: dict[str, int] = field(default_factory=dict)
    types: tuple[str, ...] | None = None


def _health(value: str) -> tuple[float, float | None, str]:
    bits = value.split()
    if not bits:
        raise RepresentationError("Missing HP evidence")
    if bits[0] == "0":
        return 0.0, None, "fnt" if "fnt" in bits else ""
    match = re.fullmatch(r"(\d+)/(\d+)", bits[0])
    if not match or int(match[2]) == 0:
        raise RepresentationError(f"Unsupported HP evidence {value}")
    return float(match[1]), float(match[2]), bits[1] if len(bits) > 1 else ""


def _effect(value: str) -> str:
    return identifier(value.split(": ", 1)[-1])


def encode(
    view: PlayerView,
    own_team: Sequence[TeamMember],
    mechanics: Mechanics,
    context: EvidenceContext | None = None,
) -> Observation:
    """Project one player's information. Full records are retained at this boundary."""
    context = context or EvidenceContext()
    if len(own_team) != 6 or len(view.opponent_sheet) != 6:
        raise RepresentationError("Expected six-member M-C teams")
    if context.game < 1:
        raise RepresentationError("Game number must be positive")
    prior = tuple(
        r
        for r in context.records
        if context.cutoff is None or r.sequence <= context.cutoff
    )
    if any(
        r.game >= context.game or r.audience not in ("public", view.player)
        for r in prior
    ):
        raise RepresentationError("Future or wrong-player prior evidence")
    if any(
        a.sequence >= b.sequence or a.game > b.game
        for a, b in zip(prior, prior[1:], strict=False)
    ):
        raise RepresentationError("Prior evidence is not chronological")
    mons = [_Mon(t.species, t.ability, t.item, t.nature, t.moves, 50) for t in own_team]
    mons += [
        _Mon(t.species, t.ability, t.item, t.nature, t.moves, t.level)
        for t in view.opponent_sheet
    ]
    for mon in mons:
        mon.current_species = mon.species
        mon.current_ability = mon.ability
        mon.current_item = mon.item
    aliases: dict[tuple[str, str], int] = {}
    own_side = view.player

    def side_offset(side: str) -> int:
        return 0 if side == own_side else 6

    for offset, side_name in ((0, own_side), (6, "p2" if own_side == "p1" else "p1")):
        for i, mon in enumerate(mons[offset : offset + 6]):
            aliases[(side_name, mon.species)] = offset + i

    def resolve(ident: str, species: str | None = None) -> int:
        side, _, name = ident.partition(": ")
        side = side[:2]
        if side not in ("p1", "p2"):
            raise RepresentationError(f"Unsupported identity {ident}")
        key = (side, name)
        if key in aliases:
            return aliases[key]
        if not species:
            species = name
        family = mechanics.species.get(identifier(species), {}).get(
            "baseSpecies", species
        )
        offset = side_offset(side)
        match = [
            i
            for i in range(offset, offset + 6)
            if mons[i].species == species
            or mechanics.species.get(identifier(mons[i].species), {}).get("baseSpecies")
            == family
        ]
        if len(match) != 1:
            raise RepresentationError(f"Unresolved identity {ident} ({species})")
        aliases[key] = match[0]
        return match[0]

    field_effects: dict[tuple[int, str], int] = {}
    weather = ""
    turn = 0

    def token(i: int) -> Features:
        mon = mons[i]
        data = mechanics.species.get(identifier(mon.current_species))
        if data is None:
            raise RepresentationError(f"Unknown species {mon.current_species}")
        cats = [
            ("species", mon.species),
            ("species", mon.current_species),
            ("ability", mon.ability),
            ("ability", mon.current_ability),
            ("item", mon.item),
            ("item", mon.current_item),
            ("nature", mon.nature),
            ("status", mon.status),
        ]
        cats += [("move", v) for v in mon.moves]
        cats += [("type", v) for v in (mon.types or data["types"])]
        cats += [("effect", v) for v in sorted(mon.effects)]
        nums: dict[str, float | None] = {
            "side": float(i // 6),
            "slot": float(i % 6) / 5,
            "active": float(mon.active + 1) / 2,
            "selected": None if mon.selected is None else float(mon.selected),
            "hp_fraction": None
            if mon.hp is None or mon.maximum is None
            else mon.hp / mon.maximum,
            "hp_precision": mon.maximum,
            "hp": mon.hp if mon.exact else None,
            "max_hp": mon.maximum if mon.exact else None,
            "level": float(mon.level),
            "weight": float(data["weightkg"]),
        }
        nums.update({f"stat_{s}": None for s in STATS})
        nums.update({f"registered_stat_{s}": None for s in STATS})
        if i < 6:
            base = mechanics.species[identifier(mon.species)]["baseStats"]
            nature = mechanics.natures[identifier(mon.nature)]
            for stat in STATS:
                value = (
                    base[stat]
                    + own_team[i].stat_points[stat]
                    + (75 if stat == "hp" else 20)
                )
                if stat != "hp":
                    factor = (
                        110
                        if nature["plus"] == stat
                        else 90
                        if nature["minus"] == stat
                        else 100
                    )
                    value = ((value * factor) & 65535) // 100
                nums[f"registered_stat_{stat}"] = float(value)
        for n, move_name in enumerate(mon.moves):
            move_data = mechanics.moves[identifier(move_name)]
            cats.extend(
                [("type", move_data["type"]), ("category", move_data["category"])]
            )
            cats.extend(("flag", x) for x in move_data["flags"])
            nums.update(
                {
                    f"move{n}_power": float(move_data["basePower"]),
                    f"move{n}_priority": float(move_data["priority"]),
                    f"move{n}_accuracy": 100.0
                    if move_data["accuracy"] is True
                    else float(move_data["accuracy"]),
                }
            )
        nums.update({f"base_{s}": float(data["baseStats"][s]) for s in STATS})
        nums.update(
            {
                f"boost_{s}": float(mon.boosts.get(s, 0)) if mon.active >= 0 else None
                for s in BOOSTS
            }
        )
        nums.update(
            {
                f"points_{s}": float(own_team[i].stat_points[s]) if i < 6 else None
                for s in STATS
            }
        )
        return features(mechanics, cats, **nums)

    def field_tokens() -> tuple[Features, ...]:
        base = features(
            mechanics,
            [("effect", weather)],
            turn=float(turn),
            game=float(context.game),
            phase=float(PHASES.index(view.phase)),
        )
        return (
            base,
            *(
                features(
                    mechanics,
                    [("effect", effect)],
                    side=float(side),
                    effect_count=float(count),
                )
                for (side, effect), count in sorted(field_effects.items())
            ),
        )

    records = list(prior)
    sequence = prior[-1].sequence if prior else 0
    for line in view.public_history:
        bits = line.split("|")[1:]
        if not bits:
            continue
        kind = bits[0]
        p = bits[1:]
        if kind not in COSMETIC | STATE_EVENTS:
            raise RepresentationError(f"Unsupported state/protocol event {kind}")
        actor = -1
        target = -1
        cats: list[tuple[str, str | None]] = []
        nums: dict[str, float | None] = {}
        if kind == "turn":
            turn = int(p[0])
        if p and re.match(r"^p[12][ab]?: ", p[0]):
            species = (
                p[1].split(",")[0] if kind in ("switch", "drag", "replace") else None
            )
            actor = resolve(p[0], species)
        before = token(actor) if actor >= 0 else None
        if kind in ("switch", "drag", "replace"):
            slot = ord(p[0][2]) - ord("a")
            side = actor // 6
            for mon in mons[side * 6 : side * 6 + 6]:
                if mon.active == slot:
                    mon.active = -1
                    mon.boosts.clear()
                    mon.effects.clear()
                    mon.types = None
            mon = mons[actor]
            mon.active = slot
            mon.selected = True
            mon.current_species = p[1].split(",")[0]
            mon.boosts.clear()
            mon.effects.clear()
            mon.types = None
            mon.hp, mon.maximum, mon.status = _health(p[2])
            mon.exact = False
        elif kind in ("-damage", "-heal"):
            mon = mons[actor]
            nums["before_fraction"] = (
                None if mon.hp is None or mon.maximum is None else mon.hp / mon.maximum
            )
            mon.hp, maximum, mon.status = _health(p[1])
            mon.maximum = maximum or mon.maximum
            mon.exact = False
            nums["after_fraction"] = (
                None if mon.maximum is None else mon.hp / mon.maximum
            )
        elif kind == "faint":
            mons[actor].hp = 0
            mons[actor].status = "fnt"
        elif kind in ("-status", "-curestatus"):
            mons[actor].status = p[1] if kind == "-status" else ""
        elif kind == "-cureteam":
            side = side_offset(p[0][:2])
            for mon in mons[side : side + 6]:
                mon.status = ""
        elif kind in ("-boost", "-unboost", "-setboost"):
            if p[1] not in BOOSTS:
                raise RepresentationError(f"Unsupported boost {p[1]}")
            mon = mons[actor]
            value = int(p[2])
            old = mon.boosts.get(p[1], 0)
            mon.boosts[p[1]] = (
                value
                if kind == "-setboost"
                else max(-6, min(6, old + value * (1 if kind == "-boost" else -1)))
            )
        elif kind in (
            "-clearboost",
            "-clearallboost",
            "-clearnegativeboost",
            "-clearpositiveboost",
            "-invertboost",
        ):
            for mon in mons if kind == "-clearallboost" else [mons[actor]]:
                mon.boosts = {
                    s: (-v if kind == "-invertboost" else v)
                    for s, v in mon.boosts.items()
                    if kind == "-invertboost"
                    or (kind == "-clearnegativeboost" and v > 0)
                    or (kind == "-clearpositiveboost" and v < 0)
                }
        elif kind in ("-copyboost", "-swapboost"):
            target = resolve(p[1])
            a = mons[actor]
            b = mons[target]
            selected = (
                p[2].replace(",", " ").split()
                if len(p) > 2 and not p[2].startswith("[")
                else list(BOOSTS)
            )
            for s in selected:
                old = a.boosts.get(s, 0)
                a.boosts[s] = b.boosts.get(s, 0)
                if kind == "-swapboost":
                    b.boosts[s] = old
        elif kind == "-weather":
            weather = "" if p[0] == "none" else _effect(p[0])
        elif kind in ("-fieldstart", "-fieldend", "-sidestart", "-sideend"):
            side = -1 if kind.startswith("-field") else side_offset(p[0][:2]) // 6
            effect = _effect(p[0] if side == -1 else p[1])
            key = (side, effect)
            if kind.endswith("start"):
                field_effects[key] = field_effects.get(key, 0) + 1
            else:
                field_effects.pop(key, None)
        elif kind in ("-start", "-end", "-singleturn", "-singlemove"):
            effect = _effect(p[1])
            mon = mons[actor]
            if effect == "typechange":
                mon.types = tuple(p[2].split("/")) if kind != "-end" else None
            elif effect == "typeadd":
                raise RepresentationError("Unsupported added-type evidence")
            elif kind == "-end":
                mon.effects.pop(effect, None)
            else:
                mon.effects[effect] = turn
        elif kind in ("-item", "-enditem"):
            mons[actor].current_item = p[1] if kind == "-item" else ""
        elif kind in ("-ability", "-endability"):
            mons[actor].current_ability = p[1] if kind == "-ability" else ""
        elif kind in ("detailschange", "-formechange"):
            mons[actor].current_species = p[1].split(",")[0]
        elif kind == "-transform":
            # Copying hidden opponent stats would require guesses; do not invent them.
            raise RepresentationError("Transform representation is unsupported")
        elif kind == "move":
            cats.append(("move", p[1]))
            move = mechanics.moves[identifier(p[1])]
            nums["priority"] = float(move["priority"])
            if len(p) > 2 and re.match(r"^p[12][ab]?: ", p[2]):
                target = resolve(p[2])
        # Preserve the complete raw structured payload as evidence, including crit,
        # miss, source and spread annotations; no sampled roll is inferred.
        if kind not in ("showteam", "poke", "player", "rule", "tier", ""):
            for annotation in p:
                if annotation.startswith("[from] "):
                    source = _effect(annotation[7:])
                    if source in ("brn", "psn", "tox"):
                        cats.append(("status", source))
                    elif f"effect:{source}" in mechanics.indices:
                        cats.append(("effect", source))
            sequence += 1
            nums.update(
                game=float(context.game),
                turn=float(turn),
                sequence=float(sequence),
                event_kind=float(EVENT_KINDS.index(kind)),
                slot=float(actor + 1) / 12,
                target=float(target + 1) / 12,
            )
            snapshots = field_tokens() + tuple(
                x
                for x in (before, token(target) if target >= 0 else None)
                if x is not None
            )
            records.append(
                Evidence(
                    context.game,
                    turn,
                    sequence,
                    "public",
                    kind,
                    tuple(p),
                    features(mechanics, cats, **nums),
                    snapshots,
                )
            )
        # Volatiles explicitly emitted as single-turn effects expire on the next turn.
        if kind == "turn":
            for mon in mons:
                for effect, started in tuple(mon.effects.items()):
                    if (
                        effect
                        in (
                            "protect",
                            "endure",
                            "wideguard",
                            "quickguard",
                            "helpinghand",
                            "followme",
                            "ragepowder",
                        )
                        and started < turn
                    ):
                        mon.effects.pop(effect)
    pokemon = []
    for i in range(12):
        f = token(i)
        if i < 6:
            registered = own_team[i]
            matches = [
                p
                for p in view.own_team
                if resolve(p.ident, p.details.split(",")[0]) == i
            ]
            if not matches and view.phase != "teampreview":
                mons[i].selected = False
                pokemon.append(token(i))
                continue
            if len(matches) != 1:
                raise RepresentationError(
                    f"Cannot match own registered member {registered.species}"
                )
            own = matches[0]
            hp, maximum, status = _health(own.condition)
            mon = mons[i]
            mon.hp = hp
            mon.maximum = maximum
            mon.exact = True
            mon.status = status
            if mon.selected is None:
                mon.selected = None if view.phase == "teampreview" else True
            mon.current_item = own.item
            f = token(i)
            values = list(f.values)
            states = list(f.states)
            for stat, value in own.stats:
                k = NUMERIC_FIELDS.index("stat_" + stat)
                values[k] = value / SCALES["stat_" + stat]
                states[k] = KNOWN
            f = Features(f.categories, tuple(values), tuple(states))
        pokemon.append(f)
    sequence += 1
    records.append(
        Evidence(
            context.game,
            view.turn,
            sequence,
            view.player,
            "own-state",
            (),
            features(
                mechanics,
                game=float(context.game),
                turn=float(view.turn),
                sequence=float(sequence),
                event_kind=float(EVENT_KINDS.index("own-state")),
            ),
            tuple(pokemon[:6]),
        )
    )
    # Candidate references use the stable registered order, not request reordering.
    request_order = [resolve(p.ident) for p in view.own_team]
    candidates = []
    for choice in choices(view):
        parts = []
        references = []
        if choice.command is None:
            parts.append(features(mechanics, action_kind=0.0))
            references.append((-1, -1))
        elif choice.command.startswith("team "):
            for slot, index in enumerate(choice.command[5:]):
                member = request_order[int(index) - 1]
                parts.append(features(mechanics, action_kind=1.0, slot=slot / 3))
                references.append((member, -1))
        else:
            for slot, command in enumerate(choice.command.split(", ")):
                words = command.split()
                actor = next(
                    (i for i, mon in enumerate(mons[:6]) if mon.active == slot),
                    request_order[slot],
                )
                kind = words[0]
                target = -1
                cats = []
                nums = {
                    "action_kind": float(
                        {"move": 2, "switch": 3, "pass": 4}.get(kind, -1)
                    ),
                    "slot": slot / 1,
                }
                if kind == "move":
                    option = view.active_options[slot].moves[int(words[1]) - 1]
                    data = mechanics.moves[identifier(option.move)]
                    cats = [("move", option.move), ("type", data["type"])]
                    nums.update(
                        pp=float(option.pp),
                        disabled=float(option.disabled),
                        priority=float(data["priority"]),
                        power=float(data["basePower"]),
                        accuracy=100.0
                        if data["accuracy"] is True
                        else float(data["accuracy"]),
                        mega=float(any(w in ("mega", "megax", "megay") for w in words)),
                    )
                    location = next(
                        (int(w) for w in words[2:] if re.fullmatch("-?[12]", w)), 0
                    )
                    target = (
                        next(
                            (
                                i
                                for i, mon in enumerate(mons)
                                if mon.active == abs(location) - 1
                                and (i < 6) == (location < 0)
                            ),
                            -1,
                        )
                        if location
                        else -1
                    )
                elif kind == "switch":
                    target = request_order[int(words[1]) - 1]
                elif kind != "pass":
                    raise RepresentationError(f"Unsupported candidate {command}")
                parts.append(features(mechanics, cats, **nums))
                references.append((actor, target))
        candidates.append(Candidate(choice, tuple(parts), tuple(references)))
    return Observation(
        SCHEMA,
        mechanics.content_id,
        view.player,
        context.game,
        view.turn,
        tuple(pokemon),
        field_tokens(),
        tuple(records),
        tuple(candidates),
    )
