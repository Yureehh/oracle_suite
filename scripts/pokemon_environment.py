"""Exercise the single-game learning interface with seeded existing random policies."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from strixia_agon.pokemon.environment import ChampionsEnv
from strixia_agon.pokemon.matches import RandomPolicy
from strixia_agon.pokemon.simulator import (
    FORMAT,
    SHOWDOWN_REVISION,
    Player,
    RequestUpdatedError,
    TeamMember,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus",
        type=Path,
        help="Frozen corpus.json; otherwise use research fixtures",
    )
    parser.add_argument(
        "--split", choices=("train", "validation", "test"), default="train"
    )
    parser.add_argument("--games", type=int, default=2)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument(
        "--showdown", type=Path, default=ROOT / "tmp/pokemon-foundation/showdown"
    )
    args = parser.parse_args()
    if not 1 <= args.games <= 100:
        parser.error("--games must be between 1 and 100")
    if args.corpus:
        manifest = json.loads(args.corpus.read_text())
        if (
            manifest.get("format") != FORMAT
            or manifest.get("showdown_revision") != SHOWDOWN_REVISION
        ):
            parser.error("Corpus must match the pinned M-C format and simulator")
        pool = [
            [TeamMember(**m) for m in t["members"]]
            for t in manifest["teams"]
            if t["split"] == args.split
        ]
    else:
        raw = json.loads(
            (ROOT / "docs/planning/pokemon/foundation/teams.json").read_text()
        )
        pool = [
            [
                TeamMember(
                    m["species"],
                    m["ability"],
                    tuple(m["moves"]),
                    m["nature"],
                    m["evs"],
                    m.get("item", ""),
                )
                for m in team
            ]
            for team in raw
        ]
    if not pool:
        parser.error("Selected corpus split has no teams")
    players: tuple[Player, Player] = ("p1", "p2")
    rng = random.Random(args.seed)
    with ChampionsEnv(args.showdown) as env:
        for game in range(args.games):
            teams = [rng.choice(pool), rng.choice(pool)]
            views = env.reset(teams, [rng.randrange(65536) for _ in range(4)])
            policies = (
                RandomPolicy(rng.randrange(2**64)),
                RandomPolicy(rng.randrange(2**64)),
            )
            selected = [
                env.actions(p).index(policy.choose(view))
                for p, policy, view in zip(players, policies, views, strict=True)
            ]
            decisions = 0
            refreshes = 0
            while True:
                try:
                    result = env.step(selected[0], selected[1])
                except RequestUpdatedError:
                    refreshed = (env.observe("p1"), env.observe("p2"))
                    for i, p in enumerate(players):
                        if refreshed[i] != views[i]:
                            selected[i] = env.actions(p).index(
                                policies[i].choose(refreshed[i])
                            )
                    views = refreshed
                    refreshes += 1
                    continue
                decisions += 1
                if result.terminated or result.truncated:
                    print(
                        json.dumps(
                            {
                                "game": game,
                                "decisions": decisions,
                                "request_refreshes": refreshes,
                                "turn": result.observations[0].turn,
                                "rewards": result.rewards,
                                "terminated": result.terminated,
                                "truncated": result.truncated,
                            }
                        )
                    )
                    break
                views = result.observations
                selected = [
                    env.actions(p).index(policy.choose(view))
                    for p, policy, view in zip(players, policies, views, strict=True)
                ]


if __name__ == "__main__":
    main()
