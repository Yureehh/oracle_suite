"""Local Champions batch coordinator; independent games run in parallel Node engines."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import platform
import signal
import struct
import subprocess
import threading
from collections.abc import Callable, Iterator
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from contextlib import contextmanager
from importlib.metadata import version
from pathlib import Path
from typing import Any

from strixia_agon.pokemon.matches import POLICY, play_game, series_result
from strixia_agon.pokemon.simulator import (
    FORMAT,
    SHOWDOWN_REVISION,
    ChampionsBattle,
    TeamMember,
)
from strixia_core.artifacts import Artifacts
from strixia_core.runs import RunError, RunStore

ROOT = Path(__file__).resolve().parents[2]


def game_seed(seed: list[int], index: int) -> list[int]:
    """Versioned per-game seeds independent of scheduling and completion order."""
    if len(seed) != 4 or any(type(x) is not int or not 0 <= x <= 65535 for x in seed):
        raise ValueError("Seed needs four unsigned 16-bit integers")
    if type(index) is not int or index < 0:
        raise ValueError("Game index must be nonnegative")
    digest = hashlib.sha256(json.dumps([seed, index]).encode()).digest()
    return list(struct.unpack(">4H", digest[:8]))


def configuration(
    teams_path: Path | None, games: int, seed: list[int], *, sets: int | None = None
) -> dict[str, Any]:
    if sets is not None:
        if type(sets) is not int or not 1 <= sets <= 333:
            raise ValueError("Sets must be an integer from 1 to 333")
        games = sets * 3
    if type(games) is not int or not 1 <= games <= 1000:
        raise ValueError("Games must be an integer from 1 to 1000")
    if teams_path:
        teams = json.loads(teams_path.read_text())
    else:
        fixture = json.loads(
            (ROOT / "docs/planning/pokemon/foundation/teams.json").read_text()
        )
        teams = [
            [
                {k: m[k] for k in ("species", "ability", "moves", "nature", "item")}
                | {"stat_points": m["evs"]}
                for m in team
            ]
            for team in fixture
        ]
    if len(teams) != 2 or any(len(team) != 6 for team in teams):
        raise ValueError("Supply two six-member teams")
    for team in teams:
        for member in team:
            TeamMember(**member)
    config = {
        "schema": 1,
        "workload": "champions-engine-default-batch",
        "format": FORMAT,
        "engine": SHOWDOWN_REVISION,
        "agon_version": version("strixia-agon"),
        "policy": "engine-default-v1",
        "seed_algorithm": "sha256-json-v1",
        "seeds": [game_seed(seed, index) for index in range(games)],
        "teams": teams,
        "games": games,
        "decision_limit": 500,
        "python_version": platform.python_version(),
        "node_version": subprocess.check_output(
            ["node", "--version"], text=True
        ).strip(),
        "npm_lock_sha256": hashlib.sha256(
            (
                ROOT / "scripts/pokemon_foundation/showdown-package-lock.json"
            ).read_bytes()
        ).hexdigest(),
        "worker_version": "local-batch-v1",
    }
    if sets is not None:
        config.update(
            workload="champions-random-bo3-v1", policy=POLICY, sets=sets, retry_limit=16
        )
    return config


def validate_runtime(config: dict[str, Any], checkout: Path) -> None:
    if (
        config.get("schema") != 1
        or config.get("workload")
        not in ("champions-engine-default-batch", "champions-random-bo3-v1")
        or config.get("format") != FORMAT
        or config.get("engine") != SHOWDOWN_REVISION
        or config.get("agon_version") != version("strixia-agon")
        or config.get("policy") != (POLICY if "sets" in config else "engine-default-v1")
        or config.get("seed_algorithm") != "sha256-json-v1"
        or config.get("worker_version") != "local-batch-v1"
    ):
        raise RunError("Unsupported or changed workload provenance")
    if config["workload"] == "champions-random-bo3-v1":
        sets = config.get("sets")
        if (
            type(sets) is not int
            or not 1 <= sets <= 333
            or config.get("games") != sets * 3
            or config.get("retry_limit") != 16
        ):
            raise RunError("Invalid set workload bounds")
    elif "sets" in config:
        raise RunError("Set count on an independent-game workload")
    games = config.get("games")
    if (
        type(games) is not int
        or not 1 <= games <= 1000
        or config.get("decision_limit") != 500
    ):
        raise RunError("Invalid batch bounds")
    seeds = config.get("seeds")
    if not isinstance(seeds, list) or len(seeds) != games:
        raise RunError("Invalid seed schedule")
    for seed in seeds:
        game_seed(seed, 0)
    if config.get("python_version") != platform.python_version():
        raise RunError("Python version differs from submission")
    node_version = subprocess.check_output(["node", "--version"], text=True).strip()
    if config.get("node_version") != node_version:
        raise RunError("Node version differs from submission")
    lock = checkout / "package-lock.json"
    expected_lock = ROOT / "scripts/pokemon_foundation/showdown-package-lock.json"
    try:
        lock_bytes = lock.read_bytes()
    except OSError as exc:
        raise RunError("Cannot inspect Showdown dependency lock") from exc
    digest = hashlib.sha256(lock_bytes).hexdigest()
    if config.get("npm_lock_sha256") != digest:
        raise RunError("Showdown dependency lock differs from submission")
    if lock_bytes != expected_lock.read_bytes():
        raise RunError("Showdown dependency lock differs from the reviewed lock")


def run_game(config: dict[str, Any], index: int, checkout: Path) -> bytes:
    teams = [[TeamMember(**member) for member in team] for team in config["teams"]]
    if "sets" in config:
        return json.dumps(
            play_game(
                checkout,
                teams,
                config["seeds"][index],
                index=index,
                decision_limit=config["decision_limit"],
                retry_limit=config["retry_limit"],
                prior_public_history=config["prior_public_history"],
            ),
            sort_keys=True,
        ).encode()
    choices: list[list[str | None]] = [["team 1234", "team 1234"]]
    with ChampionsBattle(checkout, teams, config["seeds"][index]) as battle:
        battle.step("team 1234", "team 1234")
        for _ in range(config["decision_limit"]):
            if battle.state.ended:
                break
            p1 = None if battle.state.p1.must_wait else "default"
            p2 = None if battle.state.p2.must_wait else "default"
            choices.append([p1, p2])
            battle.step(p1, p2)
        if not battle.state.ended:
            raise RuntimeError("Game exceeded decision limit")
        return json.dumps(
            {
                "schema": 1,
                "game": index,
                "seed": config["seeds"][index],
                "winner": battle.state.winner,
                "turn": battle.state.turn,
                "choices": choices,
                "public_history": battle.state.p1.public_history,
            },
            sort_keys=True,
        ).encode()


@contextmanager
def run_lock(storage: Path, run_id: str) -> Iterator[None]:
    if len(run_id) != 32 or any(c not in "0123456789abcdef" for c in run_id):
        raise RunError("Invalid run ID")
    locks = storage / "locks"
    locks.mkdir(parents=True, exist_ok=True)
    with (locks / run_id).open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RunError("Another local coordinator owns this run") from exc
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def pending_games(config: dict[str, Any], records: dict[int, Any]) -> list[int]:
    """Next missing game per set; other sets can be scheduled independently."""
    if any(type(i) is not int or not 0 <= i < config["games"] for i in records):
        raise RunError("Saved game index outside the batch")
    if "sets" not in config:
        return [i for i in range(config["games"]) if i not in records]
    pending = []
    for set_index in range(config["sets"]):
        start = set_index * 3
        indices = [i for i in range(start, start + 3) if i in records]
        if indices != list(range(start, start + len(indices))):
            raise RunError("Saved set games must form a chronological prefix")
        for i in indices:
            if (
                records[i].get("game") != i
                or records[i].get("seed") != config["seeds"][i]
            ):
                raise RunError("Saved set game identity differs from configuration")
        result = series_result([records[i]["winner"] for i in indices])
        if not result.ended:
            pending.append(start + len(indices))
    return pending


def run_status(store: RunStore, artifacts: Artifacts, run_id: str) -> dict[str, Any]:
    result = store.get(run_id)
    config = result["config"]
    if "sets" in config:
        records = {
            i: json.loads(artifacts.read(m)) for i, m in store.completed(run_id).items()
        }
        pending_games(config, records)
        result["sets"] = []
        for set_index in range(config["sets"]):
            indices = [
                i for i in range(set_index * 3, set_index * 3 + 3) if i in records
            ]
            score = series_result([records[i]["winner"] for i in indices])
            result["sets"].append(
                {
                    "set": set_index,
                    "games": indices,
                    "score": list(score.score),
                    "draws": score.draws,
                    "ended": score.ended,
                    "winner": score.winner,
                }
            )
    return result


def execute(
    storage: Path,
    run_id: str,
    checkout: Path,
    parallel: int = 2,
    *,
    resume: bool = False,
    stop: threading.Event | None = None,
    game: Callable[[dict[str, Any], int, Path], bytes] = run_game,
) -> dict[str, Any]:
    if type(parallel) is not int or not 1 <= parallel <= 32:
        raise ValueError("Parallel game count must be an integer from 1 to 32")
    stop = stop if stop is not None else threading.Event()
    storage.mkdir(parents=True, exist_ok=True)
    with run_lock(storage, run_id), RunStore(storage / "runs.sqlite3") as store:
        artifacts = Artifacts(storage / "artifacts")
        config = store.get(run_id)["config"]
        validate_runtime(config, checkout)
        finished = store.completed(run_id)
        records: dict[int, Any] = {}
        for i, manifest in finished.items():
            data = artifacts.read(manifest)
            records[i] = json.loads(data) if "sets" in config else manifest
        pending_games(config, records)
        if resume:
            store.resume(run_id)
        if store.get(run_id)["status"] == "succeeded":
            return run_status(store, artifacts, run_id)
        attempt = store.claim(run_id)
        error: str | None = None
        futures: dict[Future[bytes], int] = {}
        try:
            with ThreadPoolExecutor(max_workers=parallel) as pool:
                while True:
                    if not stop.is_set() and error is None:
                        pending = [
                            i
                            for i in pending_games(config, records)
                            if i not in futures.values()
                        ]
                        for index in pending[: parallel - len(futures)]:
                            job_config = config
                            if "sets" in config:
                                history = tuple(
                                    tuple(records[i]["public_history"])
                                    for i in range((index // 3) * 3, index)
                                )
                                job_config = config | {"prior_public_history": history}
                            futures[pool.submit(game, job_config, index, checkout)] = (
                                index
                            )
                    if not futures:
                        break
                    ready, _ = wait(futures, return_when=FIRST_COMPLETED)
                    for future in ready:
                        index = futures.pop(future)
                        try:
                            data = future.result()
                            record = json.loads(data) if "sets" in config else None
                            manifest = artifacts.write(run_id, attempt, index, data)
                            store.record_game(run_id, attempt, index, manifest)
                            records[index] = record if "sets" in config else manifest
                        except Exception as exc:
                            error = f"Game {index + 1}: {type(exc).__name__}: {exc}"
                            continue
                        try:
                            print(
                                f"{run_id}: saved game {index + 1}; {len(records)}/{config['games']} maximum slots",
                                flush=True,
                            )
                        except BrokenPipeError:
                            pass  # A closed progress reader must not change game results.
            if error:
                status = "failed"
            elif not pending_games(config, records):
                status = "succeeded"
            else:
                status = "cancelled"
            store.finish(run_id, attempt, status, error)
        except Exception as exc:
            store.finish(run_id, attempt, "failed", f"{type(exc).__name__}: {exc}")
            raise
        return run_status(store, artifacts, run_id)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--storage", type=Path, default=ROOT / "storage/local-runs")
    parser.add_argument(
        "--showdown", type=Path, default=ROOT / "tmp/pokemon-foundation/showdown"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    submit = commands.add_parser("submit")
    submit.add_argument("--teams", type=Path)
    count = submit.add_mutually_exclusive_group()
    count.add_argument("--games", type=int)
    count.add_argument(
        "--sets",
        type=int,
        help="Random-policy Bo3 sets; games within each set are sequential",
    )
    submit.add_argument("--seed", default="1,2,3,4")
    submit.add_argument("--key", required=True)
    for command in ("work", "resume", "status"):
        sub = commands.add_parser(command)
        sub.add_argument("run_id")
        if command in ("work", "resume"):
            sub.add_argument("--parallel", type=int, default=2)
    export = commands.add_parser("export")
    export.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.storage.mkdir(parents=True, exist_ok=True)
    if args.command == "submit":
        config = configuration(
            args.teams,
            args.games if args.games is not None else 8,
            [int(x) for x in args.seed.split(",")],
            sets=args.sets,
        )
        # Validate complete teams before durably queuing a run; no game choices yet.
        validate_runtime(config, args.showdown)
        with ChampionsBattle(
            args.showdown,
            [[TeamMember(**m) for m in t] for t in config["teams"]],
            config["seeds"][0],
        ):
            pass
        with RunStore(args.storage / "runs.sqlite3") as store:
            print(store.submit(config, args.key))
    elif args.command in ("work", "resume"):
        stop = threading.Event()
        previous = signal.signal(signal.SIGINT, lambda *_: stop.set())
        try:
            result = execute(
                args.storage,
                args.run_id,
                args.showdown,
                args.parallel,
                resume=args.command == "resume",
                stop=stop,
            )
            print(json.dumps(result, sort_keys=True))
            if result["status"] == "failed":
                raise SystemExit(1)
        finally:
            signal.signal(signal.SIGINT, previous)
    else:
        with RunStore(args.storage / "runs.sqlite3") as store:
            if args.command == "status":
                print(
                    json.dumps(
                        run_status(
                            store, Artifacts(args.storage / "artifacts"), args.run_id
                        ),
                        sort_keys=True,
                    )
                )
                print(f"Completed games: {sorted(store.completed(args.run_id))}")
            else:
                store.export_json(args.output)
                print(args.output)


if __name__ == "__main__":
    main()
