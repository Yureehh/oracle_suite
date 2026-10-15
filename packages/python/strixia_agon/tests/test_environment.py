"""A single-game learning loop preserves private observations and real endings."""

import json
import os
import random
from dataclasses import replace
from pathlib import Path

import pytest
from strixia_agon.pokemon.actions import JointChoice, choices
from strixia_agon.pokemon.environment import ChampionsEnv
from strixia_agon.pokemon.simulator import (
    Player,
    RequestUpdatedError,
    SimulatorError,
    TeamMember,
)

ROOT = Path(__file__).resolve().parents[4]


def inputs() -> tuple[Path, list[list[TeamMember]]]:
    checkout = Path(
        os.environ.get(
            "STRIXIA_SHOWDOWN_PATH", ROOT / "tmp/pokemon-foundation/showdown"
        )
    )
    if not (checkout / "dist/sim/index.js").exists():
        pytest.skip("Prepare the pinned engine")
    raw = json.loads((ROOT / "docs/planning/pokemon/foundation/teams.json").read_text())
    return checkout, [
        [
            TeamMember(
                m["species"],
                m["ability"],
                tuple(m["moves"]),
                m["nature"],
                m["evs"],
                gender="M",
            )
            for m in team
        ]
        for team in raw
    ]


def test_single_game_transitions_and_reproducible_reset() -> None:
    checkout, teams = inputs()
    with ChampionsEnv(checkout) as env:
        initial = env.reset(teams, (1, 2, 3, 4))
        assert len(env.actions("p1")) == 360
        assert initial[0] == env.observe("p1")
        with pytest.raises(ValueError, match="index"):
            env.step(True, 0)
        assert env.observe("p1") == initial[0]
        rng = random.Random(123)
        for _ in range(500):
            result = env.step(
                rng.randrange(len(env.actions("p1"))),
                rng.randrange(len(env.actions("p2"))),
            )
            if result.terminated or result.truncated:
                break
            assert result.rewards == (0.0, 0.0)
        assert result.terminated and not result.truncated
        assert result.rewards in ((1.0, -1.0), (-1.0, 1.0), (0.0, 0.0))
        saved = result.observations
        with pytest.raises(RuntimeError, match="reset"):
            env.step(0, 0)
        assert env.reset(teams, (1, 2, 3, 4)) == initial
        assert saved[0].phase == "end"


def test_limit_truncates_without_loss_and_hidden_worlds_match() -> None:
    checkout, teams = inputs()
    other = [list(t) for t in teams]
    other[1][0] = replace(
        other[1][0], stat_points=dict(hp=32, atk=2, **{"def": 0}, spa=0, spd=0, spe=32)
    )
    with (
        ChampionsEnv(checkout, decision_limit=1) as env,
        ChampionsEnv(checkout) as second,
    ):
        env.reset(teams, (1, 2, 3, 4))
        second.reset(other, (4, 3, 2, 1))
        assert env.observe("p1") == second.observe("p1")
        assert env.actions("p1") == second.actions("p1")
        result = env.step(0, 0)
        assert result.truncated and not result.terminated
        assert result.rewards == (0.0, 0.0)
        assert result.observations[0].phase != "end"
        with pytest.raises(RuntimeError, match="reset"):
            env.step(0, 0)


def index(env: ChampionsEnv, player: Player, command: str) -> int:
    return next(i for i, c in enumerate(env.actions(player)) if c.command == command)


@pytest.mark.parametrize("retry_limit", [16, 1])
def test_bilateral_refresh_retains_other_choice_without_transition(
    retry_limit: int,
) -> None:
    checkout, teams = inputs()
    teams[0][4] = replace(
        teams[0][4], species="Blastoise", ability="Torrent", moves=("Surf",)
    )
    for team in teams:
        for i in range(2):
            team[i] = replace(team[i], moves=("Protect",))
        team[0] = replace(
            team[0], species="Gengar", ability="Cursed Body", item="Gengarite"
        )
    with ChampionsEnv(checkout, retry_limit=retry_limit) as env:
        env.reset(teams, (1, 2, 3, 4))
        env.step(index(env, "p1", "team 1234"), index(env, "p2", "team 1234"))
        env.step(
            index(env, "p1", "move 1 mega, move 1"),
            index(env, "p2", "move 1 mega, move 1"),
        )
        other = env.observe("p2")
        with pytest.raises(RequestUpdatedError):
            env.step(
                index(env, "p1", "move 1, switch 3"),
                index(env, "p2", "move 1, switch 3"),
            )
        revealed = env.observe("p1")
        assert revealed.active_options[1].trapped
        assert env.observe("p2") == other
        with pytest.raises(ValueError, match="Retain"):
            env.step(
                index(env, "p1", "move 1, move 1"), index(env, "p2", "move 1, move 1")
            )
        if retry_limit == 1:
            with pytest.raises(SimulatorError, match="retry limit"):
                env.step(
                    index(env, "p1", "move 1, move 1"),
                    index(env, "p2", "move 1, switch 3"),
                )
            with pytest.raises(RuntimeError, match="reset"):
                env.step(0, 0)
            return
        with pytest.raises(RequestUpdatedError):
            env.step(
                index(env, "p1", "move 1, move 1"), index(env, "p2", "move 1, switch 3")
            )
        assert env.observe("p1") == revealed
        assert env.observe("p2").active_options[1].trapped
        result = env.step(
            index(env, "p1", "move 1, move 1"), index(env, "p2", "move 1, move 1")
        )
        assert (
            result.rewards == (0.0, 0.0)
            and result.observations[0].turn == revealed.turn + 1
        )


def test_failed_reset_cannot_expose_the_previous_game() -> None:
    checkout, teams = inputs()
    with ChampionsEnv(checkout) as env:
        env.reset(teams, (1, 2, 3, 4))
        bad = [list(t) for t in teams]
        bad[0][0] = replace(bad[0][0], ability="Wonder Guard")
        with pytest.raises(SimulatorError, match="Wonder Guard"):
            env.reset(bad, (1, 2, 3, 4))
        with pytest.raises(RuntimeError, match="reset"):
            env.observe("p1")
        assert env.reset(teams, (1, 2, 3, 4))[0].phase == "teampreview"


def test_ending_on_the_last_allowed_decision_is_a_real_outcome() -> None:
    checkout, teams = inputs()
    total = 0
    final = None
    with ChampionsEnv(checkout) as env:
        env.reset(teams, (1, 2, 3, 4))
        rng = random.Random(123)
        for _ in range(500):
            total += 1
            final = env.step(
                rng.randrange(len(env.actions("p1"))),
                rng.randrange(len(env.actions("p2"))),
            )
            if final.terminated:
                break
    assert final is not None and final.terminated
    with ChampionsEnv(checkout, decision_limit=total) as env:
        env.reset(teams, (1, 2, 3, 4))
        rng = random.Random(123)
        for _ in range(total):
            replay = env.step(
                rng.randrange(len(env.actions("p1"))),
                rng.randrange(len(env.actions("p2"))),
            )
        assert replay.terminated and not replay.truncated
        assert replay == final


def test_failed_action_projection_releases_engine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from strixia_agon.pokemon import environment

    checkout, teams = inputs()
    original = choices

    def broken(view: object) -> tuple[JointChoice, ...]:
        raise ValueError("Unsupported request projection")

    with ChampionsEnv(checkout) as env:
        monkeypatch.setattr(environment, "choices", broken)
        with pytest.raises(ValueError, match="projection"):
            env.reset(teams, (1, 2, 3, 4))
        assert env._battle is None
        with pytest.raises(RuntimeError, match="reset"):
            env.observe("p1")
        monkeypatch.setattr(environment, "choices", original)
        assert env.reset(teams, (1, 2, 3, 4))[0].phase == "teampreview"


def test_failed_projection_after_resolution_releases_engine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from strixia_agon.pokemon import environment

    checkout, teams = inputs()

    def broken(view: object) -> tuple[JointChoice, ...]:
        raise ValueError("Unsupported request projection")

    with ChampionsEnv(checkout) as env:
        env.reset(teams, (1, 2, 3, 4))
        monkeypatch.setattr(environment, "choices", broken)
        with pytest.raises(ValueError, match="projection"):
            env.step(0, 0)
        assert env._battle is None
        with pytest.raises(RuntimeError, match="reset"):
            env.observe("p1")
