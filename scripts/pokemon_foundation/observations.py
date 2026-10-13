"""Research projection examples, not a production observation or parser contract."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Literal

Player = Literal["p1", "p2"]
SHEET_FIELDS = ("species", "item", "ability", "moves", "nature", "gender", "level")
STATS = ("hp", "atk", "def", "spa", "spd", "spe")


@dataclass(frozen=True)
class Evidence:
    sequence: int
    game: int
    turn: int
    kind: str
    audience: str
    data: str  # Immutable JSON preserves the evidence as it was recorded.
    source: str


def own_information(request: dict[str, Any], player: Player) -> dict[str, Any]:
    """Project useful own information without copying the raw private request."""
    side = request.get("side", {})
    if side.get("id") != player:
        raise ValueError("Private request belongs to another player")
    members = []
    for mon in side.get("pokemon", []):
        member = {
            key: mon[key]
            for key in (
                "ident",
                "details",
                "condition",
                "active",
                "moves",
                "baseAbility",
                "item",
            )
            if key in mon
        }
        member["stats"] = {
            key: value for key, value in mon.get("stats", {}).items() if key in STATS
        }
        members.append(member)
    actions = []
    for active in request.get("active", []):
        actions.append(
            {
                "moves": [
                    {
                        key: move[key]
                        for key in ("move", "id", "pp", "maxpp", "target", "disabled")
                        if key in move
                    }
                    for move in active.get("moves", [])
                ],
                **{
                    key: active[key]
                    for key in ("trapped", "maybeTrapped", "canMegaEvo")
                    if key in active
                },
            }
        )
    return {
        "team": members,
        "actions": actions,
        "force_switch": request.get("forceSwitch", []),
        "preview": request.get("teamPreview", False),
        "pick_count": request.get("maxChosenTeamSize"),
    }


def project(
    ledger: tuple[Evidence, ...], player: Player, game: int, cutoff: int
) -> dict[str, Any]:
    """Rebuild a dated view; hidden state and later evidence are not inputs."""
    previous_sequence = -1
    previous_time = (0, 0)
    public: list[dict[str, Any]] = []
    knowledge: list[dict[str, Any]] = []
    beliefs: list[dict[str, Any]] = []
    own: dict[str, Any] = {}
    for event in ledger:
        if (
            event.sequence <= previous_sequence
            or (event.game, event.turn) < previous_time
        ):
            raise ValueError("Evidence must be chronological with unique sequence IDs")
        previous_sequence, previous_time = event.sequence, (event.game, event.turn)
        if event.sequence > cutoff or event.game > game:
            continue
        if event.audience not in ("public", player):
            continue
        payload = json.loads(event.data)
        record = {
            "sequence": event.sequence,
            "game": event.game,
            "turn": event.turn,
            "kind": event.kind,
            "source": event.source,
            "data": payload,
        }
        if event.kind == "request":
            if event.audience == player and event.game == game:
                own = own_information(payload, player)
            continue
        if event.kind == "belief":
            # A separately labeled illustrative assumption, never a known fact.
            if event.audience == player:
                beliefs.append(record)
            continue
        if event.kind == "sheet":
            record["data"] = {
                "player": payload["player"],
                "team": [
                    {key: mon[key] for key in SHEET_FIELDS if key in mon}
                    for mon in payload["team"]
                ],
            }
        elif event.kind in ("reveal", "damage", "order", "public_state", "outcome"):
            record["data"] = {"message": payload["message"]}
        else:
            continue  # No omniscient state, submitted choices or arbitrary payloads.
        if event.audience == "public" and event.game == game:
            public.append(record)
        if event.kind in ("sheet", "reveal", "damage", "order"):
            knowledge.append(record)
    return {
        "player": player,
        "game": game,
        "cutoff": cutoff,
        "public_history": public,
        "own_information": own,
        "known_evidence": knowledge,
        "hypothetical_beliefs": beliefs,
    }


def example(protocol: dict[str, Any]) -> dict[str, Any]:
    def ledger_for(world: dict[str, Any]) -> tuple[Evidence, ...]:
        rows: list[Evidence] = []
        for sheet in world["sheets"]:
            rows.append(
                Evidence(
                    len(rows),
                    1,
                    0,
                    "sheet",
                    "public",
                    json.dumps(sheet),
                    "engine showteam",
                )
            )
        turn = 0
        for line in world["boundary"]["0"]:
            if line.startswith("|turn|"):
                turn = int(line.split("|")[2])
            if not line.startswith("|showteam|"):
                rows.append(
                    Evidence(
                        len(rows),
                        1,
                        turn,
                        "public_state",
                        "public",
                        json.dumps({"message": line}),
                        "engine channel 0",
                    )
                )
        rows.append(
            Evidence(
                len(rows),
                1,
                1,
                "request",
                "p1",
                json.dumps(world["own_requests"][0]),
                "engine sideupdate p1",
            )
        )
        rows.append(
            Evidence(
                len(rows),
                1,
                1,
                "request",
                "p2",
                json.dumps(world["own_requests"][1]),
                "engine sideupdate p2",
            )
        )
        rows.append(
            Evidence(
                len(rows),
                1,
                1,
                "omniscient",
                "omniscient",
                json.dumps(world["omniscient"]),
                "engine snapshot",
            )
        )
        return tuple(rows)

    worlds = [ledger_for(world) for world in protocol["worlds"]]
    cutoff = worlds[0][-1].sequence
    game_one = project(worlds[0], "p1", 1, cutoff)
    same_history = game_one == project(worlds[1], "p1", 1, cutoff)
    extra: list[Evidence] = []
    turn = 0
    for line in protocol["resolved"]["0"]:
        if line.startswith("|turn|"):
            turn = int(line.split("|")[2])
        kind = "damage" if line.startswith("|-damage|") else "order"
        if kind == "order" and not line.startswith("|move|"):
            continue
        extra.append(
            Evidence(
                cutoff + len(extra) + 1,
                3,
                turn,
                kind,
                "public",
                json.dumps({"message": line}),
                "synthetic G3 reuse of G1 protocol",
            )
        )
    extended = worlds[0] + tuple(extra)
    saved = json.dumps(game_one, sort_keys=True)
    later = project(extended, "p1", 3, extended[-1].sequence)
    unchanged = saved == json.dumps(project(extended, "p1", 1, cutoff), sort_keys=True)
    if not same_history or not unchanged:
        raise AssertionError("Information boundary failed")
    return {
        "task": "003",
        "cases": {
            "hidden_world_equivalence": same_history,
            "no_future_hindsight": unchanged,
            "transient_private_reset": not later["own_information"],
        },
        "game_one": game_one,
        "game_three": later,
        "ledger": [asdict(row) for row in extended],
    }
