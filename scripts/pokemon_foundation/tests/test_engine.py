"""Behavioral integration checks against the pinned, built engine."""

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def result():
    return json.loads(
        subprocess.check_output(
            ["node", str(ROOT / "scripts/pokemon_foundation/engine.cjs")], text=True
        )
    )


def test_snapshot_seed_and_branch(result):
    for case in (
        "identical_seed",
        "snapshot_continuation",
        "branch_isolation",
        "distinct_branch",
    ):
        assert result["cases"][case], case
    assert result["cases"]["termination"]["turns"] > 0
    assert result["timings"]["warm_battles"] == 100


def test_validated_six_member_fixtures_and_invalid_rejection(result):
    assert result["validation"] == [None, None]
    assert result["cases"]["invalid_team"]
    assert all(
        request["maxChosenTeamSize"] == 4 for request in result["cases"]["preview"]
    )
    assert all(
        len(request["side"]["pokemon"]) == 6 for request in result["cases"]["preview"]
    )
    assert all(len(request["active"]) == 2 for request in result["cases"]["requests"])


def test_ots_contains_nature_but_not_allocations(result):
    sheets = result["cases"]["sheets"]
    assert [len(team) for team in sheets] == [6, 6]
    for team in sheets:
        for member in team:
            assert member["nature"]
            assert member["moves"] and member["ability"]
            assert "evs" not in member and "ivs" not in member
