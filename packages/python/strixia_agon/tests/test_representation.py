"""Player evidence is structured without revealing hidden allocations."""

import json
from dataclasses import replace
from pathlib import Path

import pytest
from strixia_agon.pokemon.mechanics import load_mechanics
from strixia_agon.pokemon.representation import (
    EvidenceContext,
    RepresentationError,
    encode,
)
from strixia_agon.pokemon.simulator import ChampionsBattle, TeamMember


def inputs() -> tuple[Path, list[list[TeamMember]]]:
    root = Path(__file__).resolve().parents[4]
    checkout = root / "tmp/pokemon-foundation/showdown"
    if not (checkout / "dist/sim/index.js").exists():
        pytest.skip("Prepare the pinned engine")
    raw = json.loads((root / "docs/planning/pokemon/foundation/teams.json").read_text())
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


def test_visible_worlds_and_mechanics() -> None:
    checkout, teams = inputs()
    mechanics = load_mechanics(checkout)
    other = [list(t) for t in teams]
    other[1][0] = replace(
        other[1][0], stat_points=dict(hp=32, atk=2, **{"def": 0}, spa=0, spd=0, spe=32)
    )
    with (
        ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as a,
        ChampionsBattle(checkout, other, (4, 3, 2, 1)) as b,
    ):
        x = encode(a.state.p1, teams[0], mechanics)
        assert x == encode(b.state.p1, teams[0], mechanics)
        assert len(x.pokemon) == 12 and len(x.candidates) == 360
        assert mechanics.species["onix"]["baseStats"]["spe"] == 70
        assert mechanics.species["regieleki"]["baseStats"]["spe"] == 200
        assert x.candidates[0].choice.command == "team 1234"


def test_unknown_protocol_is_visible_failure() -> None:
    checkout, teams = inputs()
    mechanics = load_mechanics(checkout)
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as a:
        view = replace(
            a.state.p1,
            public_history=a.state.p1.public_history
            + ("|-newmechanic|p1a: Greninja|thing",),
        )
        with pytest.raises(RepresentationError, match="newmechanic"):
            encode(view, teams[0], mechanics)


def test_full_game_projection_and_paired_mapping() -> None:
    checkout, teams = inputs()
    mechanics = load_mechanics(checkout)
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as battle:
        battle.step("team 1234", "team 1234")
        observation = encode(battle.state.p1, teams[0], mechanics)
        from strixia_agon.pokemon.representation import KNOWN, NUMERIC_FIELDS, UNKNOWN

        selected = NUMERIC_FIELDS.index("selected")
        assert [p.values[selected] for p in observation.pokemon[:6]] == [
            1,
            1,
            1,
            1,
            0,
            0,
        ]
        assert observation.pokemon[6].states[NUMERIC_FIELDS.index("hp")] == UNKNOWN
        assert observation.pokemon[0].states[NUMERIC_FIELDS.index("hp")] == KNOWN
        previous = observation
        for _ in range(100):
            if battle.state.ended:
                break
            battle.step(
                None if battle.state.p1.must_wait else "default",
                None if battle.state.p2.must_wait else "default",
            )
            observation = encode(battle.state.p1, teams[0], mechanics)
        assert battle.state.ended and not observation.candidates
        assert len(observation.history) > len(previous.history)
        assert (
            previous.history
            == encode(
                replace(
                    battle.state.p1,
                    public_history=previous.candidates[0].choice.view.public_history,
                    turn=1,
                    phase="move",
                    own_team=previous.candidates[0].choice.view.own_team,
                    active_options=previous.candidates[0].choice.view.active_options,
                ),
                teams[0],
                mechanics,
            ).history
        )


def test_game_context_resets_state_and_enforces_audience() -> None:
    from strixia_agon.pokemon.representation import NUMERIC_FIELDS, UNKNOWN

    checkout, teams = inputs()
    mechanics = load_mechanics(checkout)
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as battle:
        battle.step("team 1234", "team 1234")
        battle.step("default", "default")
        saved = encode(battle.state.p1, teams[0], mechanics)
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as fresh:
        obs = encode(
            fresh.state.p1, teams[0], mechanics, EvidenceContext(saved.history, game=2)
        )
        assert obs.history[: len(saved.history)] == saved.history
        assert obs.pokemon[6].states[NUMERIC_FIELDS.index("hp_fraction")] == UNKNOWN
        with pytest.raises(RepresentationError, match="Future"):
            encode(fresh.state.p1, teams[0], mechanics, EvidenceContext(saved.history))
        wrong = replace(saved.history[0], audience="p2")
        with pytest.raises(RepresentationError, match="wrong-player"):
            encode(
                fresh.state.p1, teams[0], mechanics, EvidenceContext((wrong,), game=2)
            )


def test_damage_order_and_unknown_zero_are_not_inferences() -> None:
    from strixia_agon.pokemon.representation import (
        KNOWN,
        NUMERIC_FIELDS,
        UNKNOWN,
        features,
    )

    checkout, teams = inputs()
    mechanics = load_mechanics(checkout)
    unknown = features(mechanics, hp=None)
    zero = features(mechanics, hp=0)
    assert unknown.values == zero.values and unknown.states != zero.states
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as battle:
        battle.step("team 1234", "team 1234")
        view = replace(
            battle.state.p1,
            public_history=battle.state.p1.public_history
            + (
                "|move|p2a: Blastoise|Surf|p1a: Greninja",
                "|-crit|p1a: Greninja",
                "|-damage|p1a: Greninja|36/100",
                "|move|p1a: Greninja|Surf|p2a: Blastoise",
            ),
        )
        obs = encode(view, teams[0], mechanics)
        damage = next(e for e in obs.history if e.kind == "-damage")
        assert damage.payload[1] == "36/100"
        assert damage.features.values[NUMERIC_FIELDS.index("after_fraction")] == 0.36
        assert obs.pokemon[6].states[NUMERIC_FIELDS.index("stat_spe")] == UNKNOWN
        assert obs.pokemon[6].states[NUMERIC_FIELDS.index("points_spe")] == UNKNOWN
        assert obs.pokemon[0].states[NUMERIC_FIELDS.index("hp")] == KNOWN
