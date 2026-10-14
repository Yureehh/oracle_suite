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
            == encode(previous.candidates[0].choice.view, teams[0], mechanics).history
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


def test_registered_stats_and_active_effect_context() -> None:
    from strixia_agon.pokemon.representation import NUMERIC_FIELDS, SCALES

    checkout, teams = inputs()
    mechanics = load_mechanics(checkout)
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as battle:
        battle.step("team 1234", "team 1234")
        view = replace(
            battle.state.p1,
            public_history=battle.state.p1.public_history
            + (
                "|-singleturn|p1a: Greninja|Protect",
                "|-sidestart|p2: p2|move: Spikes",
                "|-sidestart|p2: p2|move: Spikes",
                "|-fieldstart|move: Trick Room",
                "|turn|2",
            ),
        )
        obs = encode(view, teams[0], mechanics)
        speed = NUMERIC_FIELDS.index("registered_stat_spe")
        actual = dict(battle.state.p1.own_team[0].stats)["spe"]
        assert obs.pokemon[0].values[speed] * SCALES["registered_stat_spe"] == actual
        assert mechanics.category("effect", "protect") not in obs.pokemon[0].categories
        assert any(
            mechanics.category("effect", "trickroom") in f.categories for f in obs.field
        )
        assert any(
            f.values[NUMERIC_FIELDS.index("effect_count")] * 6 == 2 for f in obs.field
        )
        assert any(e.kind == "-singleturn" for e in obs.history)
        assert obs.history[-1].audience == "p1"


def test_padding_absence_unknown_and_not_applicable_categories() -> None:
    checkout, _ = inputs()
    mechanics = load_mechanics(checkout)
    assert mechanics.category("item", None) == 1
    assert mechanics.category("item", "") == 2
    assert mechanics.vocabulary[0] == "<pad>"
    with pytest.raises(TypeError):
        mechanics.species["onix"]["baseStats"]["spe"] = 999


def test_same_game_history_preserves_private_evidence_without_public_duplicates() -> (
    None
):
    checkout, teams = inputs()
    mechanics = load_mechanics(checkout)
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as battle:
        battle.step("team 1234", "team 1234")
        old_view = battle.state.p1
        old = encode(old_view, teams[0], mechanics)
        battle.step("default", "default")
        new = encode(battle.state.p1, teams[0], mechanics, EvidenceContext(old.history))
        assert new.history[: len(old.history)] == old.history
        assert sum(e.kind == "own-state" for e in new.history) == 2
        without = encode(battle.state.p1, teams[0], mechanics)
        assert [(e.kind, e.payload) for e in new.history if e.audience == "public"] == [
            (e.kind, e.payload) for e in without.history if e.audience == "public"
        ]
        with pytest.raises(RepresentationError, match="Future|match"):
            encode(old_view, teams[0], mechanics, EvidenceContext(new.history))
        restored = encode(
            old_view,
            teams[0],
            mechanics,
            EvidenceContext(new.history, cutoff=old.history[-1].sequence),
        )
        assert restored.history[:-1] == old.history


def test_public_event_context_never_contains_private_allocations_or_future_pp() -> None:
    from strixia_agon.pokemon.representation import NUMERIC_FIELDS

    checkout, teams = inputs()
    mechanics = load_mechanics(checkout)
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as battle:
        battle.step("team 1234", "team 1234")
        obs = encode(battle.state.p1, teams[0], mechanics)
        actor_contexts = [
            f for e in obs.history if e.audience == "public" for f in e.context
        ]
        assert all(
            f.states[NUMERIC_FIELDS.index("points_spe")] != 1 for f in actor_contexts
        )
        assert all(
            f.states[NUMERIC_FIELDS.index("move0_pp")] != 1 for f in actor_contexts
        )
        assert obs.pokemon[0].states[NUMERIC_FIELDS.index("move0_pp")] == 1
        other = encode(battle.state.p2, teams[1], mechanics)
        public = tuple(e for e in other.history if e.audience == "public")
        with pytest.raises(RepresentationError, match="perspective"):
            encode(
                battle.state.p1, teams[0], mechanics, EvidenceContext(public, game=2)
            )


def test_temporary_ability_resets_on_switch() -> None:
    checkout, teams = inputs()
    mechanics = load_mechanics(checkout)
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as b:
        b.step("team 1234", "team 1234")
        view = replace(
            b.state.p1,
            public_history=b.state.p1.public_history
            + (
                "|-ability|p2a: Blastoise|Insomnia|[from] move: Worry Seed",
                "|switch|p2a: Gardevoir|Gardevoir, L50, M|100/100",
                "|switch|p2a: Blastoise|Blastoise, L50, M|100/100",
            ),
        )
        obs = encode(view, teams[0], mechanics)
        assert obs.pokemon[6].categories[3] == mechanics.category("ability", "Torrent")


def test_candidate_actor_target_preview_and_switch_references() -> None:
    from strixia_agon.pokemon.representation import NUMERIC_FIELDS

    checkout, teams = inputs()
    mechanics = load_mechanics(checkout)
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as b:
        preview = encode(b.state.p1, teams[0], mechanics)
        assert next(
            c for c in preview.candidates if c.choice.command == "team 4132"
        ).references == ((3, -1), (0, -1), (2, -1), (1, -1))
        b.step("team 4132", "team 1234")
        obs = encode(b.state.p1, teams[0], mechanics)
        move = next(c for c in obs.candidates if c.choice.command == "move 1 1, move 1")
        assert move.references == ((3, 6), (0, -1))
        assert move.parts[0].categories[0] == mechanics.category("move", "Dragon Claw")
        assert move.parts[0].values[NUMERIC_FIELDS.index("power")] == 80 / 250
        switch = next(
            c for c in obs.candidates if c.choice.command == "switch 3, move 1"
        )
        assert switch.references == ((3, 2), (0, -1))


def test_form_change_separates_registered_and_current_ability() -> None:
    checkout, teams = inputs()
    mechanics = load_mechanics(checkout)
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as b:
        b.step("team 1234", "team 1234")
        view = replace(
            b.state.p1,
            public_history=b.state.p1.public_history
            + ("|detailschange|p2a: Blastoise|Blastoise-Mega, L50, M",),
        )
        obs = encode(view, teams[0], mechanics)
        assert obs.pokemon[6].categories[:4] == (
            mechanics.category("species", "Blastoise"),
            mechanics.category("species", "Blastoise-Mega"),
            mechanics.category("ability", "Torrent"),
            1,
        )


def test_private_refresh_cannot_enter_earlier_same_turn_observation() -> None:
    from strixia_agon.pokemon.simulator import RequestUpdatedError

    checkout, teams = inputs()
    mechanics = load_mechanics(checkout)
    for team in teams:
        for i in range(2):
            team[i] = replace(team[i], moves=("Protect",))
        team[0] = replace(
            team[0], species="Gengar", ability="Cursed Body", item="Gengarite"
        )
    teams[0][4] = replace(
        teams[0][4], species="Blastoise", ability="Torrent", moves=("Surf",)
    )
    with ChampionsBattle(checkout, teams, (1, 2, 3, 4)) as b:
        b.step("team 1234", "team 1234")
        b.step("move 1 mega, move 1", "move 1 mega, move 1")
        old = b.state.p1
        other = b.state.p2
        with pytest.raises(RequestUpdatedError):
            b.step("move 1, switch 3", "move 1, move 1")
        refreshed = encode(b.state.p1, teams[0], mechanics)
        assert old.public_history == b.state.p1.public_history
        assert b.state.p2 == other
        with pytest.raises(RepresentationError, match="Future"):
            encode(old, teams[0], mechanics, EvidenceContext(refreshed.history))
