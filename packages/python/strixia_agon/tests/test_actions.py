"""Player-visible paired decisions, exercised against the pinned engine."""

import json
import os
from pathlib import Path

import pytest
from strixia_agon.pokemon.actions import choices
from strixia_agon.pokemon.simulator import ChampionsBattle, TeamMember

ROOT = Path(__file__).resolve().parents[4]


@pytest.fixture
def checkout() -> Path:
    path = Path(
        os.environ.get(
            "STRIXIA_SHOWDOWN_PATH", ROOT / "tmp/pokemon-foundation/showdown"
        )
    )
    if not (path / "dist/sim/index.js").exists():
        pytest.skip("Prepare pinned engine")
    return path


@pytest.fixture
def teams() -> list[list[TeamMember]]:
    data = json.loads(
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
        for team in data
    ]


def test_preview_and_complete_game(
    checkout: Path, teams: list[list[TeamMember]]
) -> None:
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as battle:
        menu = choices(battle.state.p1)
        assert len(menu) == 360
        assert menu[0].command == "team 1234"
        for _ in range(40):
            if battle.state.ended:
                break
            battle.step(choices(battle.state.p1)[0], choices(battle.state.p2)[0])
        assert battle.state.ended


def test_joint_switch_conflicts_and_stale(
    checkout: Path, teams: list[list[TeamMember]]
) -> None:
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as battle:
        old = choices(battle.state.p1)[0]
        battle.step(old, choices(battle.state.p2)[0])
        menu = choices(battle.state.p1)
        assert any(a.command == "switch 3, switch 4" for a in menu)
        assert not any(a.command == "switch 3, switch 3" for a in menu)
        with pytest.raises(ValueError, match="Stale"):
            battle.step(old, choices(battle.state.p2)[0])


def test_every_initial_pair_engine_acceptance(
    checkout: Path, teams: list[list[TeamMember]]
) -> None:
    from strixia_agon.pokemon.simulator import InvalidChoiceError

    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as battle:
        battle.step("team 1234", "team 1234")
        saved = battle.state
        for choice in choices(saved.p1):
            # Offline test only: validate p1, reject p2, roll back without resolving.
            with pytest.raises(InvalidChoiceError, match="move 99"):
                battle.step(choice, "move 99, move 99")
            assert battle.state == saved


def test_hidden_trap_updates_only_own_request(
    checkout: Path, teams: list[list[TeamMember]]
) -> None:
    from dataclasses import replace

    from strixia_agon.pokemon.simulator import RequestUpdatedError

    for team in teams:
        for i in range(2):
            team[i] = replace(team[i], moves=("Protect",))
    teams[1][0] = replace(
        teams[1][0], species="Gengar", ability="Cursed Body", item="Gengarite"
    )
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as battle:
        battle.step("team 1234", "team 1234")
        battle.step("move 1, move 1", "move 1 mega, move 1")
        before = battle.state
        assert before.p1.active_options[1].maybe_trapped
        candidate = next(
            a for a in choices(before.p1) if a.command == "move 1, switch 3"
        )
        with pytest.raises(RequestUpdatedError, match="trapped"):
            battle.step(candidate, "move 1, move 1")
        assert battle.state.turn == before.turn
        assert battle.state.p1.public_history == before.p1.public_history
        assert battle.state.p2 == before.p2
        assert battle.state.p1.active_options[1].trapped
        assert candidate not in choices(battle.state.p1)
        with pytest.raises(ValueError, match="Stale"):
            battle.step(candidate, "move 1, move 1")
        battle.step("move 1, move 1", "move 1, move 1")


@pytest.mark.parametrize("stone", ["Charizardite X", "Charizardite Y"])
def test_shared_mega_and_xy_stones(
    checkout: Path, teams: list[list[TeamMember]], stone: str
) -> None:
    from dataclasses import replace

    from strixia_agon.pokemon.simulator import InvalidChoiceError

    teams[0][0] = replace(
        teams[0][0],
        species="Blastoise",
        ability="Torrent",
        item="Blastoisinite",
        moves=("Protect",),
    )
    teams[0][1] = replace(teams[0][1], item=stone, moves=("Protect",))
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as battle:
        battle.step("team 1234", "team 1234")
        menu = choices(battle.state.p1)
        assert any(a.command == "move 1 mega, move 1" for a in menu)
        assert any(a.command == "move 1, move 1 mega" for a in menu)
        assert not any((a.command or "").count("mega") > 1 for a in menu)
        with pytest.raises(InvalidChoiceError, match="only mega-evolve once"):
            battle.step("move 1 mega, move 1 mega", "default")
        battle.step("move 1, move 1 mega", "default")
        assert any(
            "|-mega|p1b: Charizard|" in line for line in battle.state.p1.public_history
        )


def test_visible_worlds_and_target_geometry(
    checkout: Path, teams: list[list[TeamMember]]
) -> None:
    from dataclasses import replace

    from strixia_agon.pokemon.simulator import InvalidChoiceError

    teams[0][0] = replace(teams[0][0], moves=("Water Pulse", "Protect"))
    teams[0][1] = replace(teams[0][1], moves=("Helping Hand", "Heat Wave"))
    other = [list(t) for t in teams]
    other[1][0] = replace(
        other[1][0], stat_points=dict(hp=32, atk=0, **{"def": 2}, spa=0, spd=0, spe=32)
    )
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as battle:
        with ChampionsBattle(checkout, other, (4, 3, 2, 1)) as hidden:
            assert choices(battle.state.p1) == choices(hidden.state.p1)
        battle.step("team 1234", "team 1234")
        menu = choices(battle.state.p1)
        assert any(a.command == "move 1 -2, move 1 -1" for a in menu)
        assert not any(a.command == "move 1 -1, move 1 -1" for a in menu)
        assert any(a.command == "move 2, move 2" for a in menu)
        for action in menu:
            with pytest.raises(InvalidChoiceError, match="move 99"):
                battle.step(action, "move 99, move 99")


def test_shortage_commanding_struggle_and_unknown_target(
    checkout: Path, teams: list[list[TeamMember]]
) -> None:
    from dataclasses import replace

    from strixia_agon.pokemon.simulator import MoveOption, SimulatorError

    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as battle:
        battle.step("team 1234", "team 1234")
        view = battle.state.p1
        own = list(view.own_team)
        own[0] = replace(own[0], condition="0 fnt")
        own[1] = replace(own[1], condition="0 fnt")
        own[3] = replace(own[3], condition="0 fnt")
        forced = replace(
            view, phase="switch", force_switch=(True, True), own_team=tuple(own)
        )
        assert {a.command for a in choices(forced)} == {
            "switch 3, pass",
            "pass, switch 3",
        }
        active = list(view.active_options)
        active[0] = replace(
            active[0],
            moves=(MoveOption("Struggle", "randomNormal", 0, False),),
            trapped=True,
        )
        own = list(view.own_team)
        own[1] = replace(own[1], commanding=True)
        struggle = replace(view, active_options=tuple(active), own_team=tuple(own))
        assert [a.command for a in choices(struggle)] == ["move 1, pass"]
        active[0] = replace(
            active[0], moves=(MoveOption("Unknown", "futureTarget", 1, False),)
        )
        with pytest.raises(SimulatorError, match="target"):
            choices(replace(struggle, active_options=tuple(active)))


def test_legal_pawmot_revival_request(
    checkout: Path, teams: list[list[TeamMember]]
) -> None:
    from dataclasses import replace

    from strixia_agon.pokemon.simulator import InvalidChoiceError

    teams[0][3] = replace(
        teams[0][3],
        species="Pawmot",
        ability="Volt Absorb",
        moves=("Revival Blessing",),
    )
    teams[0][2] = replace(teams[0][2], moves=("Protect",))
    for i, member in enumerate(teams[1]):
        teams[1][i] = replace(member, moves=(*member.moves, "Protect"))
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as battle:
        battle.step("team 1234", "team 1234")
        for _ in range(12):
            if battle.state.phase == "move" and battle.state.p1.own_team[
                0
            ].ident.endswith("Pawmot"):
                battle.step("move 1, move 1", "move 2, move 2")
                break
            battle.step(
                None if battle.state.p1.must_wait else "default",
                None if battle.state.p2.must_wait else "default",
            )
        assert battle.state.p1.own_team[0].reviving
        assert battle.state.p2.must_wait
        assert {a.command for a in choices(battle.state.p1)} == {
            "switch 3, pass",
            "switch 4, pass",
        }
        with pytest.raises(InvalidChoiceError, match="fainted"):
            battle.step("switch 2, pass", None)
        battle.step(choices(battle.state.p1)[0], choices(battle.state.p2)[0])
        assert "fnt" not in battle.state.p1.own_team[2].condition


@pytest.mark.parametrize("selection", [0, 1])
def test_real_double_faint_single_reserve(
    checkout: Path, teams: list[list[TeamMember]], selection: int
) -> None:
    with ChampionsBattle(checkout, teams, (0, 2, 3, 4)) as battle:
        battle.step("team 1234", "team 1234")
        for _ in range(10):
            view = battle.state.p2
            if view.phase == "switch" and view.force_switch == (True, True):
                reserves = [
                    m
                    for m in view.own_team
                    if not m.active and "fnt" not in m.condition
                ]
                if len(reserves) == 1:
                    break
            battle.step(
                None if battle.state.p1.must_wait else "default",
                None if battle.state.p2.must_wait else "default",
            )
        assert [a.command for a in choices(view)] == [
            "switch 4, pass",
            "pass, switch 4",
        ]
        battle.step(choices(battle.state.p1)[0], choices(view)[selection])
        assert battle.state.phase == "move"


def test_imprison_refreshes_only_submitting_player(
    checkout: Path, teams: list[list[TeamMember]]
) -> None:
    from dataclasses import replace

    from strixia_agon.pokemon.simulator import RequestUpdatedError

    teams[0][0] = replace(teams[0][0], moves=("Protect", "Weather Ball"))
    teams[0][1] = replace(teams[0][1], moves=("Protect", "Heat Wave"))
    teams[1][0] = replace(
        teams[1][0],
        species="Gengar",
        ability="Cursed Body",
        moves=("Imprison", "Protect"),
    )
    teams[1][1] = replace(teams[1][1], moves=("Protect",))
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as battle:
        battle.step("team 1234", "team 1234")
        battle.step("move 1, move 1", "move 1, move 1")
        before = battle.state
        assert before.p1.active_options[0].moves[0].disabled
        assert not before.p1.active_options[1].moves[0].disabled
        assert before.p1.active_options[1].maybe_disabled
        candidate = next(
            a for a in choices(before.p1) if a.command == "move 2 1, move 1"
        )
        with pytest.raises(RequestUpdatedError, match="disabled"):
            battle.step(candidate, "move 2, move 1")
        assert battle.state.turn == before.turn
        assert battle.state.p1.public_history == before.p1.public_history
        assert battle.state.p2 == before.p2
        assert battle.state.p1.active_options[1].moves[0].disabled
        assert not before.p1.active_options[1].moves[0].disabled
        assert all(
            not (a.command or "").endswith(", move 1") for a in choices(battle.state.p1)
        )
        battle.step("move 2 1, move 2", "move 2, move 1")
