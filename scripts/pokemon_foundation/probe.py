"""Bounded local research; never connect to a public battle server."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import os
import platform
import signal
import socket
import subprocess
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
STORAGE = ROOT / "tmp/pokemon-foundation"
SHOWDOWN_REV = "3a766f2cfb5e51c1e428cfe87d0dba91a8f01640"
POKE_ENV_REV = "7ff6212e4e738efd46f1ea52035b37a8bba1e386"
FORMAT = "gen9championsvgc2026regmcbo3"


def engine(task: str) -> dict[str, Any]:
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=STORAGE / "showdown", text=True
    ).strip()
    if revision != SHOWDOWN_REV:
        raise RuntimeError(f"Wrong engine revision: {revision}")
    return dict(
        json.loads(
            subprocess.check_output(
                [
                    "node",
                    str(
                        Path(__file__).with_name(
                            {
                                "001": "engine.cjs",
                                "002": "rules.cjs",
                                "003": "visibility.cjs",
                            }[task]
                        )
                    ),
                ],
                text=True,
            )
        )
    )


async def client(packed: list[str]) -> dict[str, Any]:
    from poke_env.battle import AbstractBattle
    from poke_env.player import Player
    from poke_env.player.battle_order import BattleOrder
    from poke_env.ps_client import AccountConfiguration, ServerConfiguration

    observations: list[dict[str, Any]] = []

    class DefaultPlayer(Player):
        def choose_move(self, battle: AbstractBattle) -> BattleOrder:
            observations.append(
                {
                    "turn": battle.turn,
                    "own": {key: mon.stats for key, mon in battle.team.items()},
                    "opponent": {
                        key: {
                            "stats": mon.stats,
                            "nature": str(mon.nature),
                            "moves": list(mon.moves),
                            "ability": mon.ability,
                        }
                        for key, mon in battle.opponent_team.items()
                    },
                }
            )
            return self.choose_default_move()

        def teampreview(self, battle: AbstractBattle) -> str:
            return "/team 1234"

    players = [
        DefaultPlayer(
            account_configuration=AccountConfiguration(f"Foundation{i}", None),
            battle_format=FORMAT,
            team=packed[i],
            accept_open_team_sheet=True,
            server_configuration=ServerConfiguration(
                "ws://127.0.0.1:8765/showdown/websocket",
                "http://127.0.0.1:8765/action.php?",
            ),
            log_level=30,
        )
        for i in range(2)
    ]
    samples: list[float] = []
    try:
        for _ in range(3):
            started = time.perf_counter()
            await asyncio.wait_for(
                players[0].battle_against(players[1], n_battles=1), 60
            )
            samples.append((time.perf_counter() - started) * 1000)
        return {
            "status": "supported",
            "sets": 3,
            "games": len(players[0].battles),
            "timings_ms": samples,
            "observations": observations,
        }
    except TimeoutError:
        return {
            "status": "unsupported",
            "reason": "60-second set timeout",
            "completed_games": len(players[0].battles),
            "timings_ms": samples,
            "observations": observations,
        }
    finally:
        await asyncio.gather(*(p.ps_client.stop_listening() for p in players))  # type: ignore[no-untyped-call]


@contextmanager
def local_server() -> Iterator[float]:
    with socket.socket() as sock:
        if sock.connect_ex(("127.0.0.1", 8765)) == 0:
            raise RuntimeError("Port 8765 is occupied; refusing to use another server")
    started = time.perf_counter()
    with (STORAGE / "server.log").open("w") as log:
        process = subprocess.Popen(
            ["node", "pokemon-showdown", "start", "8765"],
            cwd=STORAGE / "showdown",
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
        try:
            while True:
                with socket.socket() as sock:
                    if sock.connect_ex(("127.0.0.1", 8765)) == 0:
                        break
                if process.poll() is not None or time.perf_counter() - started > 15:
                    raise RuntimeError("Local server did not start; inspect server.log")
                time.sleep(0.1)
            yield (time.perf_counter() - started) * 1000
        finally:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass  # Startup may have failed before cleanup.
            process.wait(timeout=10)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", choices=["001", "002", "003"])
    parser.add_argument(
        "--client", action="store_true", help="Starts an isolated local server"
    )
    args = parser.parse_args()
    started = time.perf_counter()
    result = engine(args.task)
    if args.task == "003":
        from observations import example

        result["projection"] = example(result)
    if args.client and args.task != "001":
        parser.error("--client applies only to 001")
    if args.client:
        with local_server() as server_ms:
            result["server_startup_ms"] = server_ms
            result["client"] = asyncio.run(client(result.pop("packed_teams")))
    result["versions"] = {
        "python": platform.python_version(),
        "npm": subprocess.check_output(["npm", "--version"], text=True).strip(),
        "uv": subprocess.check_output(["uv", "--version"], text=True).strip(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "showdown_revision": SHOWDOWN_REV,
        "poke_env_revision": POKE_ENV_REV,
        "dependencies": {
            dist.metadata["Name"]: dist.version
            for dist in importlib.metadata.distributions()
        },
    }
    result["evidence_utc"] = datetime.now(UTC).isoformat()
    result["inputs_sha256"] = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [
            ROOT / "docs/planning/pokemon/foundation/teams.json",
            Path(__file__).with_name("uv.lock"),
            Path(__file__).with_name("showdown-package-lock.json"),
        ]
    }
    result["wall_ms"] = (time.perf_counter() - started) * 1000
    STORAGE.mkdir(parents=True, exist_ok=True)
    output = STORAGE / f"{args.task}.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(output)


if __name__ == "__main__":
    main()
