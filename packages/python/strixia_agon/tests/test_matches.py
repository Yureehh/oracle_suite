"""Seeded policies, real game execution and pinned series scoring."""

import json
from dataclasses import replace
from pathlib import Path

import pytest
from strixia_agon.pokemon import matches
from strixia_agon.pokemon.actions import JointChoice, choices
from strixia_agon.pokemon.matches import RandomPolicy, play_game, series_result
from strixia_agon.pokemon.simulator import (
    BattleState,
    ChampionsBattle,
    RequestUpdatedError,
    SimulatorError,
    TeamMember,
)

ROOT = Path(__file__).resolve().parents[4]
CHECKOUT = ROOT / "tmp/pokemon-foundation/showdown"


def teams() -> list[list[TeamMember]]:
    fixture = json.loads(
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
                item=m["item"],
                gender="M",
            )
            for m in team
        ]
        for team in fixture
    ]


def test_policy_seed_and_visible_menu() -> None:
    with ChampionsBattle(CHECKOUT, teams(), [1, 2, 3, 4]) as battle:
        view = battle.state.p1
        first, second = RandomPolicy(42), RandomPolicy(42)
        menu = choices(view)
        selected = [first.choose(view) for _ in range(100)]
        assert selected == [second.choose(view) for _ in range(100)]
        assert all(choice in menu for choice in selected)
        assert len({c.command for c in selected}) > 50
        waiting = replace(view, must_wait=True)
        assert first.choose(waiting).command is None
        with pytest.raises(ValueError, match="ended"):
            first.choose(replace(view, phase="end"))


@pytest.mark.parametrize(
    ("outcomes", "ended", "winner", "score"),
    [
        ([], False, None, (0, 0)),
        (["p1", "p1"], True, "p1", (2, 0)),
        (["p1", "p2", "p2"], True, "p2", (1, 2)),
        (["p1", None], False, None, (1, 0)),
        (["p1", None, None], True, "p1", (1, 0)),
        (["p1", "p2", None], True, None, (1, 1)),
        ([None, None, None], True, None, (0, 0)),
    ],
)
def test_series_scoring(
    outcomes: list[str | None], ended: bool, winner: str | None, score: tuple[int, int]
) -> None:
    result = series_result(outcomes)
    assert (result.ended, result.winner, result.score) == (ended, winner, score)


def test_series_rejects_results_after_early_end() -> None:
    with pytest.raises(ValueError, match="ended"):
        series_result(["p1", "p1", "p2"])
    with pytest.raises(ValueError):
        series_result(["invalid"])


def test_real_random_game_repeatability_and_history() -> None:
    prior = (("|move|p2a: Opponent|Tackle|p1a: Ally",),)
    first = play_game(CHECKOUT, teams(), [1, 2, 3, 4], prior_public_history=prior)
    second = play_game(CHECKOUT, teams(), [1, 2, 3, 4], prior_public_history=prior)
    assert first == second
    assert first["winner"] in ("p1", "p2", None)
    assert first["prior_public_history"] == prior
    assert first["choices"][0][0].startswith("team ")
    assert first["policy_seeds"][0] != first["policy_seeds"][1]
    assert all(c != "default" for pair in first["choices"] for c in pair)
    assert prior == (("|move|p2a: Opponent|Tackle|p1a: Ally",),)
    with pytest.raises(RuntimeError, match="decision limit"):
        play_game(CHECKOUT, teams(), [1, 2, 3, 4], decision_limit=1)


def test_real_trapping_refresh_retries_only_changed_player(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = teams()
    for team in fixture:
        for i in range(2):
            team[i] = replace(team[i], moves=("Protect",))
    fixture[1][0] = replace(
        fixture[1][0], species="Gengar", ability="Cursed Body", item="Gengarite"
    )

    def prepared(
        checkout: Path, teams: list[list[TeamMember]], seed: list[int]
    ) -> ChampionsBattle:
        battle = ChampionsBattle(checkout, teams, seed)
        battle.step("team 1234", "team 1234")
        battle.step("move 1, move 1", "move 1 mega, move 1")
        return battle

    monkeypatch.setattr(matches, "ChampionsBattle", prepared)
    result = play_game(CHECKOUT, fixture, [1, 2, 3, 4])
    first = result["rejections"][0]
    assert first["players"] == ["p1"] and "trapped" in first["error"]
    assert first["choices"][1] == result["choices"][0][1]
    assert result["winner"] in ("p1", "p2", None)
    with pytest.raises(SimulatorError, match="retry limit"):
        play_game(CHECKOUT, fixture, [1, 2, 3, 4], retry_limit=0)


def test_bilateral_trap_refresh_keeps_previously_revealed_request() -> None:
    fixture = teams()
    fixture[0][4] = replace(
        fixture[0][4], species="Blastoise", ability="Torrent", moves=("Surf",)
    )
    for team in fixture:
        for i in range(2):
            team[i] = replace(team[i], moves=("Protect",))
        team[0] = replace(
            team[0], species="Gengar", ability="Cursed Body", item="Gengarite"
        )
    with ChampionsBattle(CHECKOUT, fixture, [1, 2, 3, 4]) as battle:
        battle.step("team 1234", "team 1234")
        battle.step("move 1 mega, move 1", "move 1 mega, move 1")
        with pytest.raises(RequestUpdatedError):
            battle.step("move 1, switch 3", "move 1, switch 3")
        revealed = battle.state.p1
        assert revealed.active_options[1].trapped
        with pytest.raises(RequestUpdatedError):
            battle.step("move 1, move 1", "move 1, switch 3")
        assert battle.state.p1 == revealed
        assert battle.state.p2.active_options[1].trapped


def test_unchanged_request_update_fails_without_another_submission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []

    class Unchanged(ChampionsBattle):
        def step(
            self, p1: JointChoice | str | None, p2: JointChoice | str | None
        ) -> BattleState:
            calls.append((p1, p2))
            raise RequestUpdatedError("No changed frame")

    monkeypatch.setattr(matches, "ChampionsBattle", Unchanged)
    with pytest.raises(SimulatorError, match="unchanged request"):
        play_game(CHECKOUT, teams(), [1, 2, 3, 4])
    assert len(calls) == 1
