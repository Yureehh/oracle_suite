"""Single-game two-player learning interface; no trainer or tensor schema."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from .actions import JointChoice, choices
from .simulator import (
    ChampionsBattle,
    Player,
    PlayerView,
    RequestUpdatedError,
    SimulatorError,
    TeamMember,
)


@dataclass(frozen=True)
class Transition:
    observations: tuple[PlayerView, PlayerView]
    rewards: tuple[float, float]
    terminated: bool
    truncated: bool


class ChampionsEnv:
    """A trusted collector submits both menu indices simultaneously.

    Policies receive only observe(player) and actions(player). Request updates
    produce no learning transition: refresh the changed player and retain the
    other's selection. Engine failures are errors, never scored game outcomes.
    """

    def __init__(
        self, checkout: Path, *, decision_limit: int = 500, retry_limit: int = 16
    ) -> None:
        if type(decision_limit) is not int or decision_limit < 1:
            raise ValueError("Decision limit must be a positive integer")
        if type(retry_limit) is not int or retry_limit < 0:
            raise ValueError("Retry limit must be a nonnegative integer")
        self._checkout = checkout
        self._limit = decision_limit
        self._retry_limit = retry_limit
        self._battle: ChampionsBattle | None = None
        self._views: tuple[PlayerView, PlayerView] | None = None
        self._menus: tuple[tuple[JointChoice, ...], tuple[JointChoice, ...]] = ((), ())
        self._retained: tuple[JointChoice | None, JointChoice | None] = (None, None)
        self._decisions = 0
        self._refreshes = 0

    def reset(
        self, teams: Sequence[Sequence[TeamMember]], seed: Sequence[int]
    ) -> tuple[PlayerView, PlayerView]:
        self.close()
        self._views = None
        self._menus = ((), ())
        self._retained = (None, None)
        self._battle = ChampionsBattle(self._checkout, teams, seed)
        views = (self._battle.state.p1, self._battle.state.p2)
        self._menus = self._menus_for(views)
        self._views = views
        self._decisions = self._refreshes = 0
        return self._views

    def _menus_for(
        self,
        views: tuple[PlayerView, PlayerView],
        changed: Sequence[int] = (0, 1),
    ) -> tuple[tuple[JointChoice, ...], tuple[JointChoice, ...]]:
        try:
            return (
                choices(views[0]) if 0 in changed else self._menus[0],
                choices(views[1]) if 1 in changed else self._menus[1],
            )
        except Exception:
            self.close()
            self._views = None
            self._menus = ((), ())
            raise

    @staticmethod
    def _index(player: Player) -> int:
        if player not in ("p1", "p2"):
            raise ValueError("Player must be p1 or p2")
        return 0 if player == "p1" else 1

    def observe(self, player: Player) -> PlayerView:
        if self._views is None:
            raise RuntimeError("Call reset before observing")
        return self._views[self._index(player)]

    def actions(self, player: Player) -> tuple[JointChoice, ...]:
        self.observe(player)
        return self._menus[self._index(player)]

    def step(self, p1: int, p2: int) -> Transition:
        if self._battle is None:
            raise RuntimeError("Call reset before another step")
        pair = []
        for index, action in enumerate((p1, p2)):
            if type(action) is not int or not 0 <= action < len(self._menus[index]):
                raise ValueError("Action index is outside the current legal menu")
            choice = self._menus[index][action]
            if self._retained[index] is not None and choice != self._retained[index]:
                raise ValueError("Retain the unchanged player's submitted choice")
            pair.append(choice)
        previous = self._views
        try:
            state = self._battle.step(pair[0], pair[1])
        except RequestUpdatedError as exc:
            refreshed = (self._battle.state.p1, self._battle.state.p2)
            changed = (
                [i for i in range(2) if refreshed[i] != previous[i]] if previous else []
            )
            self._refreshes += 1
            if not changed or self._refreshes > self._retry_limit:
                self.close()
                raise SimulatorError(
                    "Unavailable-choice retry limit or unchanged request"
                ) from exc
            self._retained = (
                None if 0 in changed else pair[0],
                None if 1 in changed else pair[1],
            )
            self._views = refreshed
            self._menus = self._menus_for(refreshed, changed)
            raise
        except SimulatorError:
            self.close()
            raise
        self._views = (state.p1, state.p2)
        self._menus = ((), ()) if state.ended else self._menus_for(self._views)
        self._retained = (None, None)
        self._refreshes = 0
        self._decisions += 1
        truncated = self._decisions >= self._limit and not state.ended
        rewards = (0.0, 0.0)
        if state.ended and state.winner:
            rewards = (1.0, -1.0) if state.winner == "p1" else (-1.0, 1.0)
        result = Transition(self._views, rewards, state.ended, truncated)
        if state.ended or truncated:
            self.close()
        return result

    def close(self) -> None:
        if self._battle is not None:
            self._battle.close()
            self._battle = None

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
