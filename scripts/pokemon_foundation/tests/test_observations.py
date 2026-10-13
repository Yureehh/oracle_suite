"""Leakage, privacy and retrospective evidence tests for research examples."""

import json
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest
from observations import Evidence, example, project

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def protocol():
    return json.loads(
        subprocess.check_output(
            ["node", str(ROOT / "scripts/pokemon_foundation/visibility.cjs")], text=True
        )
    )


def test_two_actual_hidden_worlds(protocol):
    a, b = protocol["worlds"]
    assert a["omniscient"] != b["omniscient"]
    assert a["own_requests"][1] != b["own_requests"][1]
    assert a["preview"]["1"] == b["preview"]["1"]
    assert a["boundary"]["1"] == b["boundary"]["1"]
    assert example(protocol)["cases"]["hidden_world_equivalence"]


def test_public_damage_does_not_contain_opponent_exact_hp(protocol):
    public = protocol["resolved"]["0"]
    private = protocol["resolved"]["2"]
    shared = [line for line in public if line.startswith("|-damage|p2")]
    exact = [line for line in private if line.startswith("|-damage|p2")]
    assert shared and exact and shared != exact
    assert all("/100" in line or "0 fnt" in line for line in shared)


def test_future_reveals_do_not_rewrite_game_one(protocol):
    result = example(protocol)
    ledger = tuple(Evidence(**row) for row in result["ledger"])
    saved = json.dumps(result["game_one"], sort_keys=True)
    assert saved == json.dumps(
        project(ledger, "p1", 1, result["game_one"]["cutoff"]), sort_keys=True
    )
    assert len(result["game_three"]["known_evidence"]) > len(
        result["game_one"]["known_evidence"]
    )
    assert result["game_three"]["own_information"] == {}
    assert not any(row["game"] == 1 for row in result["game_three"]["public_history"])


def test_opponent_private_request_and_hidden_choices_are_excluded(protocol):
    result = example(protocol)
    ledger = tuple(Evidence(**row) for row in result["ledger"])
    cutoff = result["game_one"]["cutoff"]
    original = project(ledger, "p1", 1, cutoff)
    poisoned = tuple(
        replace(
            row,
            data=json.dumps(
                {
                    "opponent_spread": 32,
                    "submitted_choice": "switch 4",
                    "rng": [9, 8, 7, 6],
                }
            ),
        )
        if row.audience in ("p2", "omniscient") and row.game == 1
        else row
        for row in ledger
    )
    assert project(poisoned, "p1", 1, cutoff) == original
    assert original["own_information"]["team"][0]["stats"]["spe"] == 191
    assert all(row["kind"] != "request" for row in original["known_evidence"])


def test_beliefs_remain_separate_and_private():
    ledger = (
        Evidence(
            0, 1, 1, "damage", "public", '{"message":"HP fell to 70/100"}', "observed"
        ),
        Evidence(
            1,
            2,
            0,
            "belief",
            "p1",
            '{"range":"illustrative, uncomputed"}',
            "assumption",
        ),
    )
    first = project(ledger, "p1", 1, 0)
    later = project(ledger, "p1", 2, 1)
    assert first["hypothetical_beliefs"] == []
    assert len(later["hypothetical_beliefs"]) == 1
    assert len(later["known_evidence"]) == 1
    assert project(ledger, "p2", 2, 1)["hypothetical_beliefs"] == []


def test_wrong_private_owner_is_rejected():
    event = Evidence(
        0, 1, 0, "request", "p1", '{"side":{"id":"p2"}}', "invalid provenance"
    )
    with pytest.raises(ValueError, match="another player"):
        project((event,), "p1", 1, 0)


def test_nonchronological_ledger_is_rejected():
    event = Evidence(2, 2, 0, "reveal", "public", '{"message":"revealed"}', "observed")
    with pytest.raises(ValueError, match="chronological"):
        project((event, replace(event, sequence=1, game=1)), "p1", 2, 2)


def test_ots_projection_drops_stats_even_if_supplied():
    payload = {
        "player": "p2",
        "team": [
            {
                "species": "Blastoise",
                "nature": "Modest",
                "evs": {"hp": 32},
                "ivs": {"hp": 31},
                "stats": {"hp": 186},
            }
        ],
    }
    event = Evidence(
        0, 1, 0, "sheet", "public", json.dumps(payload), "synthetic hostile payload"
    )
    sheet = project((event,), "p1", 1, 0)["known_evidence"][0]["data"]["team"][0]
    assert sheet == {"species": "Blastoise", "nature": "Modest"}
