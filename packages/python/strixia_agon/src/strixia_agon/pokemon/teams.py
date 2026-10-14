"""Showdown/PokePaste imports with explicit Champions-native missing data."""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .simulator import SHOWDOWN_REVISION, STATS, SimulatorError, TeamMember

MAX_PASTE_BYTES = 128 * 1024
_LABELS = dict(zip(("HP", "Atk", "Def", "SpA", "SpD", "Spe"), STATS, strict=True))


def _points(text: str, *, ivs: bool = False) -> tuple[tuple[str, int], ...]:
    values = dict.fromkeys(STATS, 31 if ivs else 0)
    seen = set()
    for allocation in text.split("/"):
        match = re.fullmatch(r"\s*(\d+)\s+(HP|Atk|Def|SpA|SpD|Spe)\s*", allocation)
        if not match:
            raise ValueError(f"Invalid allocation: {allocation.strip()}")
        value, label = match.groups()
        if label in seen:
            raise ValueError(f"Duplicate allocation: {label}")
        seen.add(label)
        values[_LABELS[label]] = int(value)
    if any(v > (31 if ivs else 32) for v in values.values()):
        raise ValueError(
            "Allocation exceeds native Champions boundary; no EV conversion"
        )
    if not ivs and sum(values.values()) > 66:
        raise ValueError("Stat-point total exceeds 66")
    return tuple(values.items())


@dataclass(frozen=True)
class ImportedMember:
    species: str
    nickname: str
    gender: str
    item: str
    ability: str | None
    nature: str | None
    stat_points: tuple[tuple[str, int], ...] | None
    moves: tuple[str, ...]
    metadata: tuple[tuple[str, str], ...] = ()

    def complete(self) -> TeamMember:
        """Convert only explicit, complete inputs; never invent unknown spreads."""
        if self.stat_points is None:
            raise ValueError(f"{self.species}: missing stat points")
        if not self.ability or not self.nature:
            raise ValueError(f"{self.species}: missing ability or nature")
        for key, value in self.metadata:
            if key == "IVs" and any(v != 31 for _, v in _points(value, ivs=True)):
                raise ValueError("Champions IVs must be 31; no legacy conversion")
        return TeamMember(
            self.species,
            self.ability,
            self.moves,
            self.nature,
            dict(self.stat_points),
            self.item,
            self.gender,
        )


def import_team(text: str) -> tuple[ImportedMember, ...]:
    """Read classic export text; a missing EVs line remains unknown.

    In M-C the historical EVs label carries native stat points. Within an explicit
    allocation line, omitted stats are zero according to the export convention.
    """
    if len(text.encode("utf-8")) > MAX_PASTE_BYTES:
        raise ValueError("Team paste exceeds 128 KiB")
    blocks = re.split(r"\n\s*\n", text.replace("\r\n", "\n").strip())
    result = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        header, *body = lines
        name, sep, item = header.partition(" @ ")
        gender = ""
        match = re.search(r" \(([MF])\)$", name)
        if match:
            gender = match[1]
            name = name[: match.start()]
        nickname = ""
        match = re.fullmatch(r"(.+) \(([^()]+)\)", name)
        if match:
            nickname, name = match.groups()
        if not name or any(c in name for c in "[]=@"):
            raise ValueError(f"Invalid Pokémon header: {header}")
        fields: dict[str, str] = {}
        moves = []
        for line in body:
            if line.startswith("-"):
                move = line[1:].strip()
                if not move or "/" in move:
                    raise ValueError("Move alternatives must be resolved explicitly")
                moves.append(move)
                continue
            if line.endswith(" Nature"):
                key, value = "Nature", line.removesuffix(" Nature")
            else:
                key, delim, value = line.partition(":")
                if not delim or key not in (
                    "Ability",
                    "EVs",
                    "IVs",
                    "Level",
                    "Shiny",
                    "Happiness",
                    "Tera Type",
                    "Dynamax Level",
                    "Gigantamax",
                ):
                    raise ValueError(f"Unknown team line: {line}")
                value = value.strip()
            if key in fields:
                raise ValueError(f"Duplicate field: {key}")
            if not value:
                raise ValueError(f"Empty field: {key}")
            fields[key] = value
        if not 1 <= len(moves) <= 4:
            raise ValueError("Supply one to four moves per Pokémon")
        if "Level" in fields and not re.fullmatch(r"[0-9]+", fields["Level"]):
            raise ValueError("Level must be an integer")
        if "Level" in fields and not 1 <= int(fields["Level"]) <= 100:
            raise ValueError("Level must be between 1 and 100")
        if "IVs" in fields:
            _points(fields["IVs"], ivs=True)
        result.append(
            ImportedMember(
                name,
                nickname,
                gender,
                item if sep else "",
                fields.get("Ability"),
                fields.get("Nature"),
                _points(fields["EVs"]) if "EVs" in fields else None,
                tuple(moves),
                tuple(
                    (k, v)
                    for k, v in fields.items()
                    if k not in ("Ability", "Nature", "EVs")
                ),
            )
        )
    if not result or len(result) > 6:
        raise ValueError("Import one to six Pokémon; simulation requires six")
    return tuple(result)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self,
        req: Request,
        fp: object,
        code: int,
        msg: str,
        headers: object,
        newurl: str,
    ) -> None:
        raise ValueError("PokePaste redirects are not accepted")


def read_team(source: Path | str) -> tuple[ImportedMember, ...]:
    """Read a local file or a bounded HTTPS PokePaste; no arbitrary URL fetches."""
    if isinstance(source, Path):
        with source.open("rb") as file:
            data = file.read(MAX_PASTE_BYTES + 1)
    else:
        match = re.fullmatch(r"https://pokepast\.es/([0-9a-f]{16})(?:/raw|/)?", source)
        if not match:
            raise ValueError("Supply a canonical HTTPS PokePaste URL")
        try:
            with build_opener(_NoRedirect()).open(
                f"https://pokepast.es/{match[1]}/raw",
                timeout=15,
            ) as response:
                data = response.read(MAX_PASTE_BYTES + 1)
        except (HTTPError, URLError, TimeoutError) as exc:
            raise ValueError(f"Cannot retrieve PokePaste: {exc}") from exc
    if len(data) > MAX_PASTE_BYTES:
        raise ValueError("Team paste exceeds 128 KiB")
    return import_team(data.decode("utf-8"))


def validate_team(
    checkout: Path, team: tuple[TeamMember, ...]
) -> tuple[TeamMember, ...]:
    """Return normalized team data or the pinned validator's rejection reasons."""
    if len(team) != 6:
        raise ValueError("Simulation requires six Pokémon")
    try:
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=checkout,
            text=True,
            timeout=15,
            stderr=subprocess.PIPE,
        ).strip()
        if revision != SHOWDOWN_REVISION:
            raise SimulatorError(f"Expected pinned Showdown {SHOWDOWN_REVISION}")
        process = subprocess.run(
            [
                "node",
                str(Path(__file__).with_name("engine_bridge.cjs")),
                str(checkout.resolve()),
            ],
            input=json.dumps(
                {"op": "validate", "team": [m._engine_set() for m in team]}
            )
            + "\n",
            capture_output=True,
            text=True,
            timeout=15,
            check=True,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise SimulatorError("Cannot run pinned team validator") from exc
    reply = json.loads(process.stdout)
    if not reply["ok"]:
        raise ValueError(reply["error"])
    return tuple(
        TeamMember(
            m["species"],
            m["ability"],
            tuple(m["moves"]),
            m["nature"],
            m["evs"],
            m.get("item", ""),
            m.get("gender", ""),
        )
        for m in reply["frame"]["team"]
    )


def team_data(team: Sequence[TeamMember]) -> list[dict[str, Any]]:
    """JSON-safe native members, without engine EV/IV compatibility fields."""
    return [
        {
            "species": m.species,
            "ability": m.ability,
            "moves": list(m.moves),
            "nature": m.nature,
            "stat_points": dict(m.stat_points),
            "item": m.item,
            "gender": m.gender,
        }
        for m in team
    ]
