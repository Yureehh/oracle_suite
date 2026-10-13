"""Real pinned-engine behavior and local boundary failure tests."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, replace
from pathlib import Path

import pytest
from strixia_agon.pokemon.simulator import (
    FORMAT,
    ChampionsBattle,
    InvalidChoiceError,
    SimulatorError,
    TeamMember,
)

ROOT = Path(__file__).resolve().parents[4]


@pytest.fixture
def teams() -> list[list[TeamMember]]:
    fixtures = json.loads(
        (ROOT / "docs/planning/pokemon/foundation/teams.json").read_text()
    )
    return [
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
        for team in fixtures
    ]


@pytest.fixture
def checkout() -> Path:
    path = Path(
        os.environ.get(
            "STRIXIA_SHOWDOWN_PATH", ROOT / "tmp/pokemon-foundation/showdown"
        )
    )
    if not (path / "dist/sim/index.js").exists():
        pytest.skip("Prepare the pinned engine with prepare.sh --engine-only")
    return path


def finish(battle: ChampionsBattle) -> None:
    battle.step("team 1234", "team 1234")
    for _ in range(100):
        if battle.state.ended:
            return
        battle.step(
            None if battle.state.p1.must_wait else "default",
            None if battle.state.p2.must_wait else "default",
        )
    pytest.fail("Fixture did not terminate")


def test_seed_repeatability_and_process_cleanup(
    checkout: Path, teams: list[list[TeamMember]]
) -> None:
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as first:
        process = first._process
        finish(first)
        state = first.state
        assert state.winner in ("p1", "p2")
        assert any("0 fnt" in mon.condition for mon in state.p2.own_team)
    assert process.poll() is not None
    assert not first._reader.is_alive()
    first.close()
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as second:
        finish(second)
        assert second.state == state
    with pytest.raises(SimulatorError, match="ended"):
        second.step("default", "default")


def test_invalid_pair_rolls_back_and_can_retry(
    checkout: Path, teams: list[list[TeamMember]]
) -> None:
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as battle:
        battle.step("team 1234", "team 1234")
        saved = battle.state
        with pytest.raises(InvalidChoiceError, match="move 99"):
            battle.step("default", "move 99, move 99")
        assert battle.state == saved
        recovered = battle.step("default", "default")
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as clean:
        clean.step("team 1234", "team 1234")
        assert clean.step("default", "default") == recovered


def test_hidden_worlds_and_saved_views(
    checkout: Path, teams: list[list[TeamMember]]
) -> None:
    other = [list(team) for team in teams]
    other[1][0] = replace(
        other[1][0], stat_points=dict(hp=32, atk=2, **{"def": 0}, spa=0, spd=0, spe=32)
    )
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as first:
        saved = first.state.p1
        with ChampionsBattle(checkout, other, (4, 3, 2, 1)) as second:
            assert second.state.p1 == saved
            assert second.state.p2.own_team != first.state.p2.own_team
        finish(first)
        assert saved.phase == "teampreview" and saved.turn == 0
        assert "stat_points" not in asdict(saved.opponent_sheet[0])
        assert "stats" not in asdict(saved.opponent_sheet[0])
        assert all(
            "/100" in line or "0 fnt" in line
            for line in first.state.p1.public_history
            if line.startswith("|-damage|p2")
        )


@pytest.mark.parametrize("value", [-1, 33, 0.5, True])
def test_native_allocation_guard(teams: list[list[TeamMember]], value: int) -> None:
    points = dict(teams[0][0].stat_points)
    points["hp"] = value
    with pytest.raises(ValueError, match="integers"):
        replace(teams[0][0], stat_points=points)


def test_validation_and_runtime_failures(
    checkout: Path, teams: list[list[TeamMember]]
) -> None:
    with pytest.raises(ValueError, match="Only"):
        ChampionsBattle(checkout, teams, (1, 2, 3, 4), format_id=FORMAT + "invalid")
    with pytest.raises(ValueError, match="total"):
        replace(
            teams[0][0],
            stat_points=dict(hp=32, atk=32, **{"def": 0}, spa=0, spd=0, spe=3),
        )
    bad = [list(team) for team in teams]
    bad[0][0] = replace(bad[0][0], ability="Wonder Guard")
    with pytest.raises(SimulatorError, match="Wonder Guard"):
        ChampionsBattle(checkout, bad, (1, 2, 3, 4))
    with pytest.raises(SimulatorError, match="inspect"):
        ChampionsBattle(checkout / "missing", teams, (1, 2, 3, 4))
    with pytest.raises(SimulatorError, match="launch"):
        ChampionsBattle(checkout, teams, (1, 2, 3, 4), node="/missing/node")


@pytest.mark.parametrize("mode", ["malformed", "frame", "timeout", "exit"])
def test_broken_transport_cleans_up(
    checkout: Path, teams: list[list[TeamMember]], tmp_path: Path, mode: str
) -> None:
    executable = tmp_path / "fake-node"
    code = {
        "malformed": 'print("not json", flush=True)',
        "frame": 'print(\'{"ok":true,"frame":{}}\', flush=True)',
        "timeout": "time.sleep(5)",
        "exit": "sys.exit(1)",
    }[mode]
    executable.write_text(
        f"#!{sys.executable}\nimport sys, time\nsys.stdin.readline()\n{code}\n"
    )
    executable.chmod(0o700)
    with pytest.raises(SimulatorError):
        ChampionsBattle(
            checkout, teams, (1, 2, 3, 4), node=str(executable), timeout=0.5
        )


def test_forced_replacements_are_explicit(
    checkout: Path, teams: list[list[TeamMember]]
) -> None:
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as battle:
        battle.step("team 1234", "team 1234")
        switched = battle.step("default", "default")
        assert switched.phase == "switch"
        assert switched.p1.force_switch == (False, True)
        assert switched.p2.force_switch == (False, True)
        with pytest.raises(InvalidChoiceError):
            battle.step("move 1, move 1", "default")
        assert battle.state == switched
        assert battle.step("default", "default").phase == "move"
