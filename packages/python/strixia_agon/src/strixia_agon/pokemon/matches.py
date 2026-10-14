"""Uniform paired-action baseline and bounded Champions games/series."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from random import Random
from typing import Any

from .actions import JointChoice, choices
from .simulator import (
    ChampionsBattle,
    PlayerView,
    RequestUpdatedError,
    SimulatorError,
    TeamMember,
)

POLICY = "uniform-joint-v1"


class RandomPolicy:
    """Uniform over complete visible menu entries, not over strategic categories."""

    def __init__(self, seed: int) -> None:
        self._random = Random(seed)

    def choose(self, view: PlayerView) -> JointChoice:
        menu = choices(view)
        if not menu:
            raise ValueError("Cannot choose in an ended game")
        return menu[0] if len(menu) == 1 else self._random.choice(menu)


@dataclass(frozen=True)
class SeriesResult:
    score: tuple[int, int]
    draws: int
    ended: bool
    winner: str | None


def series_result(outcomes: Sequence[str | None]) -> SeriesResult:
    """Mirror the pinned server: three game slots, ties lower the win threshold."""
    score = [0, 0]
    draws = 0
    ended = False
    winner = None
    for index, outcome in enumerate(outcomes):
        if ended:
            raise ValueError("Results supplied after series ended")
        if outcome is None:
            draws += 1
        elif outcome in ("p1", "p2"):
            score[0 if outcome == "p1" else 1] += 1
        else:
            raise ValueError("Unknown game winner")
        threshold = (3 - draws) // 2 + 1
        winner = next(
            (
                p
                for p, wins in zip(("p1", "p2"), score, strict=True)
                if wins >= threshold
            ),
            None,
        )
        ended = winner is not None or index == 2
    return SeriesResult((score[0], score[1]), draws, ended, winner)


def play_game(
    checkout: Path,
    teams: Sequence[Sequence[TeamMember]],
    seed: Sequence[int],
    *,
    index: int = 0,
    decision_limit: int = 500,
    retry_limit: int = 16,
    prior_public_history: tuple[tuple[str, ...], ...] = (),
) -> dict[str, Any]:
    """Play one seeded game; previous public evidence is recorded, not inferred.

    Only the trusted controller sees both player views. Each policy receives its
    own immutable view. Restriction refreshes resample only the changed player.
    """
    if type(decision_limit) is not int or decision_limit < 1:
        raise ValueError("Decision limit must be positive")
    if type(retry_limit) is not int or retry_limit < 0:
        raise ValueError("Retry limit must be nonnegative")
    policy_seeds = [
        int.from_bytes(
            hashlib.sha256(json.dumps([list(seed), p, POLICY]).encode()).digest()[:8],
            "big",
        )
        for p in ("p1", "p2")
    ]
    policies = [RandomPolicy(s) for s in policy_seeds]
    commands: list[list[str | None]] = []
    rejections: list[dict[str, Any]] = []
    with ChampionsBattle(checkout, teams, seed) as battle:
        for _ in range(decision_limit):
            if battle.state.ended:
                break
            views = [battle.state.p1, battle.state.p2]
            pair = [
                policy.choose(view)
                for policy, view in zip(policies, views, strict=True)
            ]
            for retry in range(retry_limit + 1):
                try:
                    battle.step(pair[0], pair[1])
                    break
                except RequestUpdatedError as exc:
                    refreshed = [battle.state.p1, battle.state.p2]
                    changed = [i for i in range(2) if refreshed[i] != views[i]]
                    rejections.append(
                        {
                            "turn": battle.state.turn,
                            "choices": [c.command for c in pair],
                            "players": [views[i].player for i in changed],
                            "error": str(exc),
                        }
                    )
                    if not changed or retry == retry_limit:
                        raise SimulatorError(
                            "Unavailable-choice retry limit or unchanged request"
                        ) from exc
                    for i in changed:
                        pair[i] = policies[i].choose(refreshed[i])
                    views = refreshed
            commands.append([c.command for c in pair])
        if not battle.state.ended:
            raise RuntimeError("Game exceeded decision limit")
        return {
            "schema": 1,
            "game": index,
            "seed": list(seed),
            "policy": POLICY,
            "policy_seeds": policy_seeds,
            "winner": battle.state.winner,
            "turn": battle.state.turn,
            "choices": commands,
            "rejections": rejections,
            "public_history": battle.state.p1.public_history,
            "prior_public_history": prior_public_history,
        }
