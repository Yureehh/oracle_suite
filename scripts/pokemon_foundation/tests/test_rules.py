"""Preserve measured validator behavior, including gaps rather than hiding them."""

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def result():
    return json.loads(
        subprocess.check_output(
            ["node", str(ROOT / "scripts/pokemon_foundation/rules.cjs")], text=True
        )
    )


def test_allocation_boundaries_and_fractional_gap(result):
    cases = {case["name"]: case for case in result["cases"]}
    for name in ("zero_neutral", "max_total", "fractional"):
        assert cases[name]["status"] == "accepted", name
    assert cases["fractional"]["normalized"][0]["evs"]["hp"] == 0.5
    for name in ("zero_serious", "over_stat", "negative", "over_total", "nonmax_iv"):
        assert cases[name]["status"] == "rejected", name
        assert cases[name]["reasons"]
    assert result["boundaries"]["total"] == 66


def test_hand_calculations_and_nature_rounding(result):
    examples = {case["nature"]: case for case in result["examples"]}
    assert examples["Hardy"]["actual"]["hp"] == 149
    assert examples["Timid"]["actual"]["spe"] == 191
    assert examples["Timid"]["actual"]["atk"] == 132
    assert examples["Modest"]["actual"]["spa"] == 135
    assert all(case["matches"] for case in result["examples"])


def test_illegal_teams_and_level_adjustment(result):
    cases = {case["name"]: case for case in result["cases"]}
    for name in (
        "unavailable_species",
        "invalid_ability",
        "invalid_move",
        "unavailable_item",
        "duplicate_item",
        "four_members",
        "seven_members",
        "level_101",
    ):
        assert cases[name]["status"] == "rejected", name
        assert cases[name]["reasons"]
    for level in (1, 50, 100):
        assert cases[f"level_{level}"]["normalized"][0]["level"] == 50
