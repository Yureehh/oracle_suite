"""Complete paired choices from the player's request, without hidden-state probes."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations, product

from .simulator import PlayerView, SimulatorError


@dataclass(frozen=True)
class JointChoice:
    view: PlayerView
    command: str | None


def _targets(kind: str, slot: int) -> tuple[int, ...]:
    own = -(slot + 1)
    ally = -(2 - slot)
    if kind in ("normal", "any"):
        return (ally, 1, 2)
    if kind == "adjacentAlly":
        return (ally,)
    if kind == "adjacentAllyOrSelf":
        return (own, ally)
    if kind == "adjacentFoe":
        return (1, 2)
    if kind in (
        "self",
        "all",
        "allAdjacent",
        "allAdjacentFoes",
        "allySide",
        "allyTeam",
        "foeSide",
        "randomNormal",
        "scripted",
    ):
        return (0,)
    raise SimulatorError(f"Unsupported move target: {kind}")


def choices(view: PlayerView) -> tuple[JointChoice, ...]:
    """Known-valid menu; uncertain restrictions can update a submitted request."""
    if view.phase == "end":
        return ()
    if view.must_wait:
        return (JointChoice(view, None),)
    if view.phase == "teampreview":
        count = view.preview_pick_count
        if count != 4 or len(view.own_team) != 6:
            raise SimulatorError("Unsupported M-C preview size")
        return tuple(
            JointChoice(view, "team " + "".join(map(str, order)))
            for order in permutations(range(1, 7), count)
        )
    if view.phase not in ("move", "switch"):
        raise SimulatorError(f"Unsupported request phase: {view.phase}")
    reserves = tuple(
        i + 1
        for i, m in enumerate(view.own_team)
        if not m.active and "fnt" not in m.condition
    )
    options: list[list[tuple[str, int | None, bool]]] = []
    forced = sum(
        required and not view.own_team[i].reviving
        for i, required in enumerate(view.force_switch)
    )
    possible: list[tuple[str, int | None, bool]]
    for slot in range(2):
        mon = view.own_team[slot]
        if view.phase == "switch":
            if mon.reviving:
                options.append(
                    [
                        (f"switch {i + 1}", None, False)
                        for i, m in enumerate(view.own_team)
                        if "fnt" in m.condition
                    ]
                )
            elif not view.force_switch[slot]:
                options.append([("pass", None, False)])
            else:
                possible = [(f"switch {i}", i, False) for i in reserves]
                if len(reserves) < forced:
                    possible.append(("pass", None, False))
                options.append(possible)
            continue
        if "fnt" in mon.condition or mon.commanding:
            options.append([("pass", None, False)])
            continue
        active = view.active_options[slot]
        possible = []
        mechanics = ("",) + tuple(
            flag
            for flag, supported in (
                ("mega", active.can_mega_evolve),
                ("megax", active.can_mega_evolve_x),
                ("megay", active.can_mega_evolve_y),
            )
            if supported
        )
        for index, move in enumerate(active.moves, 1):
            # Locked and Struggle requests can omit PP; availability is in disabled.
            if move.disabled:
                continue
            for target in _targets(move.target, slot):
                for mechanic in mechanics:
                    text = (
                        f"move {index}"
                        + (f" {target}" if target else "")
                        + (f" {mechanic}" if mechanic else "")
                    )
                    possible.append((text, None, bool(mechanic)))
        if not active.trapped:
            possible.extend((f"switch {i}", i, False) for i in reserves)
        options.append(possible)
    result = []
    for pair in product(*options):
        switches = [p[1] for p in pair if p[1] is not None]
        if len(set(switches)) != len(switches) or sum(p[2] for p in pair) > 1:
            continue
        if view.phase == "switch" and len(switches) != min(forced, len(reserves)):
            continue
        result.append(JointChoice(view, ", ".join(p[0] for p in pair)))
    if not result:
        raise SimulatorError("Player request produced no supported choices")
    return tuple(result)
