"""Run one local M-C game from Python using engine-default demonstration choices."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from strixia_agon.pokemon.simulator import ChampionsBattle, TeamMember

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--showdown", type=Path, default=ROOT / "tmp/pokemon-foundation/showdown"
    )
    parser.add_argument(
        "--teams", type=Path, help="JSON containing two native team lists"
    )
    parser.add_argument(
        "--seed", default="1,2,3,4", help="Four comma-separated integers"
    )
    args = parser.parse_args()
    if args.teams:
        data = json.loads(args.teams.read_text())
    else:
        fixtures = json.loads(
            (ROOT / "docs/planning/pokemon/foundation/teams.json").read_text()
        )
        # Research fixture field evs already contains native Champions stat points.
        data = [
            [
                {k: mon[k] for k in ("species", "ability", "moves", "nature", "item")}
                | {"stat_points": mon["evs"]}
                for mon in team
            ]
            for team in fixtures
        ]
    teams = [[TeamMember(**member) for member in team] for team in data]
    parts = [int(value) for value in args.seed.split(",")]
    if len(parts) != 4:
        parser.error("--seed needs four integers")
    with ChampionsBattle(args.showdown, teams, tuple(parts)) as battle:
        print(
            "M-C doubles, one game; engine-default choices are not a strategic policy."
        )
        print(f"Preview: select {battle.state.p1.preview_pick_count} of six.")
        battle.step("team 1234", "team 1234")
        for _ in range(500):
            if battle.state.ended:
                print(
                    f"Finished on turn {battle.state.turn}: winner={battle.state.winner or 'tie'}"
                )
                return
            battle.step(
                None if battle.state.p1.must_wait else "default",
                None if battle.state.p2.must_wait else "default",
            )
        raise RuntimeError("Demonstration exceeded 500 decision boundaries")


if __name__ == "__main__":
    main()
