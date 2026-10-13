"""A synchronous, local Champions engine boundary; not an RL environment."""

from __future__ import annotations

import json
import math
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from types import MappingProxyType
from typing import Any, Literal, Self, TextIO

SHOWDOWN_REVISION = "3a766f2cfb5e51c1e428cfe87d0dba91a8f01640"
FORMAT = "gen9championsvgc2026regmcbo3"
Player = Literal["p1", "p2"]
STATS = ("hp", "atk", "def", "spa", "spd", "spe")


class SimulatorError(RuntimeError):
    """Engine validation, protocol or process failure."""


class InvalidChoiceError(SimulatorError):
    """A rejected choice pair; the decision boundary remains unchanged."""


@dataclass(frozen=True)
class TeamMember:
    species: str
    ability: str
    moves: tuple[str, ...]
    nature: str
    stat_points: Mapping[str, int]
    item: str = ""
    gender: str = ""

    def __post_init__(self) -> None:
        points = dict(self.stat_points)
        if set(points) != set(STATS):
            raise ValueError("Supply all six native stat-point fields")
        if any(type(v) is not int or not 0 <= v <= 32 for v in points.values()):
            raise ValueError("Stat points must be integers from 0 to 32")
        if sum(points.values()) > 66:
            raise ValueError("Stat-point total exceeds 66")
        if not 1 <= len(self.moves) <= 4 or any(not m for m in self.moves):
            raise ValueError("Supply one to four moves")
        if not self.species or not self.ability or not self.nature:
            raise ValueError("Species, ability and nature are required")
        object.__setattr__(self, "stat_points", MappingProxyType(points))
        object.__setattr__(self, "moves", tuple(self.moves))

    def _engine_set(self) -> dict[str, Any]:
        return {
            "species": self.species,
            "ability": self.ability,
            "moves": self.moves,
            "nature": self.nature,
            "item": self.item,
            "gender": self.gender,
            "level": 50,
            "evs": dict(self.stat_points),
            "ivs": dict.fromkeys(STATS, 31),
        }


@dataclass(frozen=True)
class SheetMember:
    species: str
    ability: str
    moves: tuple[str, ...]
    nature: str
    item: str
    gender: str
    level: int


@dataclass(frozen=True)
class OwnPokemon:
    ident: str
    details: str
    condition: str
    active: bool
    stats: tuple[tuple[str, int], ...]
    moves: tuple[str, ...]
    ability: str
    item: str


@dataclass(frozen=True)
class MoveOption:
    move: str
    target: str
    pp: int
    disabled: bool


@dataclass(frozen=True)
class ActiveOptions:
    moves: tuple[MoveOption, ...]
    trapped: bool
    maybe_trapped: bool
    can_mega_evolve: bool


@dataclass(frozen=True)
class PlayerView:
    player: Player
    turn: int
    phase: str
    public_history: tuple[str, ...]
    opponent_sheet: tuple[SheetMember, ...]
    own_team: tuple[OwnPokemon, ...]
    active_options: tuple[ActiveOptions, ...]
    force_switch: tuple[bool, ...]
    must_wait: bool
    preview_pick_count: int | None


@dataclass(frozen=True)
class BattleState:
    turn: int
    phase: str
    ended: bool
    winner: str | None
    p1: PlayerView
    p2: PlayerView

    def view(self, player: Player) -> PlayerView:
        if player not in ("p1", "p2"):
            raise ValueError("Player must be p1 or p2")
        return self.p1 if player == "p1" else self.p2


def _read_lines(stream: TextIO, output: Queue[str | None]) -> None:
    try:
        for line in stream:
            output.put(line)
    finally:
        output.put(None)


class ChampionsBattle:
    """One engine process per game; pass only view(player) to that player's policy."""

    def __init__(
        self,
        showdown_path: Path,
        teams: Sequence[Sequence[TeamMember]],
        seed: Sequence[int],
        *,
        node: str = "node",
        timeout: float = 10,
        format_id: str = FORMAT,
    ) -> None:
        if format_id != FORMAT:
            raise ValueError(f"Only {FORMAT} is supported")
        if len(teams) != 2 or any(len(team) != 6 for team in teams):
            raise ValueError("Supply two six-member teams")
        if len(seed) != 4 or any(
            type(v) is not int or not 0 <= v <= 65535 for v in seed
        ):
            raise ValueError("Seed requires four unsigned 16-bit integers")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("Timeout must be finite and positive")
        self._timeout = timeout
        self._history: tuple[str, ...] = ()
        self._closed = False
        checkout = showdown_path.resolve()
        try:
            revision = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=checkout,
                text=True,
                stderr=subprocess.PIPE,
                timeout=timeout,
            ).strip()
        except (OSError, subprocess.SubprocessError) as exc:
            raise SimulatorError("Cannot inspect Showdown checkout") from exc
        if revision != SHOWDOWN_REVISION:
            raise SimulatorError(
                f"Expected Showdown {SHOWDOWN_REVISION}, got {revision}"
            )
        self._output: Queue[str | None] = Queue()
        try:
            self._process = subprocess.Popen(
                [
                    node,
                    str(Path(__file__).with_name("engine_bridge.cjs")),
                    str(checkout),
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                bufsize=1,
            )
        except OSError as exc:
            raise SimulatorError("Cannot launch Node engine") from exc
        assert self._process.stdout is not None
        self._reader = Thread(
            target=_read_lines, args=(self._process.stdout, self._output), daemon=True
        )
        self._reader.start()
        try:
            response = self._exchange(
                {
                    "op": "start",
                    "seed": seed,
                    "teams": [
                        [member._engine_set() for member in team] for team in teams
                    ],
                }
            )
            self.state = self._project(response)
        except (KeyError, TypeError, ValueError, StopIteration) as exc:
            self.close()
            raise SimulatorError("Malformed initial engine frame") from exc
        except Exception:
            self.close()
            raise

    def _exchange(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self._closed:
            raise SimulatorError("Battle is closed")
        assert self._process.stdin is not None
        try:
            self._process.stdin.write(json.dumps(payload) + "\n")
            self._process.stdin.flush()
            line = self._output.get(timeout=self._timeout)
            if line is None:
                raise SimulatorError("Engine exited before replying")
            response = json.loads(line)
            if not isinstance(response, dict) or type(response.get("ok")) is not bool:
                raise SimulatorError("Malformed engine reply")
            if not response["ok"]:
                error = str(response.get("error", "Engine rejected command"))
                if payload["op"] == "step":
                    raise InvalidChoiceError(error)
                raise SimulatorError(error)
            if not isinstance(response.get("frame"), dict):
                raise SimulatorError("Missing engine frame")
            return dict(response["frame"])
        except InvalidChoiceError:
            raise
        except (OSError, Empty, ValueError, SimulatorError) as exc:
            self.close()
            if isinstance(exc, SimulatorError):
                raise
            raise SimulatorError("Engine communication failed or timed out") from exc

    def _project(self, frame: dict[str, Any]) -> BattleState:
        self._history += tuple(frame["events"])
        views = []
        for i, player in enumerate(("p1", "p2")):
            request = frame["requests"][i] or {}
            if request.get("side"):
                if request["side"]["id"] != player:
                    raise SimulatorError("Private request owner mismatch")
            side = request.get("side", {})
            own = tuple(
                OwnPokemon(
                    m["ident"],
                    m["details"],
                    m["condition"],
                    m.get("active", False),
                    tuple(
                        (k, int(v)) for k, v in m.get("stats", {}).items() if k in STATS
                    ),
                    tuple(m.get("moves", [])),
                    m.get("baseAbility", ""),
                    m.get("item", ""),
                )
                for m in side.get("pokemon", [])
            )
            sheet = next(s["team"] for s in frame["sheets"] if s["player"] != player)
            opponent = tuple(
                SheetMember(
                    m["species"],
                    m["ability"],
                    tuple(m["moves"]),
                    m["nature"],
                    m["item"],
                    m.get("gender", ""),
                    m["level"],
                )
                for m in sheet
            )
            options = tuple(
                ActiveOptions(
                    tuple(
                        MoveOption(
                            m["move"], m["target"], m["pp"], m.get("disabled", False)
                        )
                        for m in active.get("moves", [])
                    ),
                    active.get("trapped", False),
                    active.get("maybeTrapped", False),
                    bool(active.get("canMegaEvo", False)),
                )
                for active in request.get("active", [])
            )
            views.append(
                PlayerView(
                    "p1" if i == 0 else "p2",
                    frame["turn"],
                    frame["phase"],
                    self._history,
                    opponent,
                    own,
                    options,
                    tuple(request.get("forceSwitch", [])),
                    request.get("wait", False),
                    request.get("maxChosenTeamSize"),
                )
            )
        return BattleState(
            frame["turn"],
            frame["phase"],
            frame["ended"],
            frame["winner"],
            views[0],
            views[1],
        )

    def step(self, p1: str | None, p2: str | None) -> BattleState:
        if self.state.ended:
            raise SimulatorError("Battle has ended")
        if any(
            choice is not None
            and (not isinstance(choice, str) or "\n" in choice or "\r" in choice)
            for choice in (p1, p2)
        ):
            raise ValueError("Choices must be single-line strings or None for waiting")
        frame = self._exchange({"op": "step", "choices": [p1, p2]})
        try:
            self.state = self._project(frame)
        except (KeyError, TypeError, ValueError, StopIteration, SimulatorError) as exc:
            self.close()
            raise SimulatorError("Malformed engine frame") from exc
        return self.state

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=2)
        self._reader.join(timeout=2)
        for stream in (self._process.stdin, self._process.stdout, self._process.stderr):
            if stream is not None:
                stream.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
