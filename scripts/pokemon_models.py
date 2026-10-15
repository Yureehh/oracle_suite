"""Measure untrained model inference, with real menus and synthetic long histories."""

from __future__ import annotations

import argparse
import json
import math
import multiprocessing as mp
import platform
import resource
import statistics
import subprocess
import sys
import time
import tracemalloc
from dataclasses import replace
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Any

import torch
from strixia_agon.pokemon.mechanics import load_mechanics
from strixia_agon.pokemon.models import PARTS, WIDTH, PolicyValueModel, batch
from strixia_agon.pokemon.representation import (
    NUMERIC_FIELDS,
    SCALES,
    SCHEMA,
    Observation,
    encode,
)
from strixia_agon.pokemon.simulator import (
    FORMAT,
    SHOWDOWN_REVISION,
    ChampionsBattle,
    TeamMember,
)

ROOT = Path(__file__).resolve().parents[1]
WARMUP = 5
PASSES = 50


def synthetic_history(observation: Observation, length: int) -> Observation:
    """Repeat real evidence with updated chronology; this is synthetic workload."""
    if not observation.history or length < 1:
        raise ValueError("Synthetic histories need source evidence and positive length")
    records = []
    for i in range(length):
        record = observation.history[i % len(observation.history)]
        values = list(record.features.values)
        values[NUMERIC_FIELDS.index("sequence")] = (i + 1) / SCALES["sequence"]
        records.append(
            replace(
                record,
                sequence=i + 1,
                features=replace(record.features, values=tuple(values)),
            )
        )
    return replace(observation, history=tuple(records))


def reserve_output(path: Path) -> None:
    """Only create a new Git-ignored destination, atomically refusing overwrite."""
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", str(path.resolve())], cwd=ROOT, check=False
    )
    if ignored.returncode != 0:
        raise ValueError("Output directory must be ignored by Git (for example tmp/)")
    path.mkdir(parents=True, exist_ok=False)


def _synchronize(device: str) -> None:
    if device == "mps":
        torch.mps.synchronize()


def _case(
    connection: Connection,
    observation: Observation,
    vocabulary: int,
    kind: str,
    size: int,
    device: str,
    seed: int,
) -> None:
    """One isolated case; process-level memory peaks include model/input setup."""
    try:
        torch.set_num_threads(1)
        torch.manual_seed(seed)
        tracemalloc.start()
        model = PolicyValueModel(vocabulary, kind).to(device).eval()
        start = time.perf_counter()
        tensors = batch([observation] * size, device)
        _synchronize(device)
        batching = time.perf_counter() - start
        durations = []
        with torch.inference_mode():
            for _ in range(WARMUP):
                model(tensors)
                _synchronize(device)
            for _ in range(PASSES):
                _synchronize(device)
                start = time.perf_counter()
                output = model(tensors)
                _synchronize(device)
                durations.append(time.perf_counter() - start)
            if (
                not torch.isfinite(output.value).all()
                or not torch.isfinite(output.logits[tensors.candidate_mask]).all()
            ):
                raise RuntimeError("Nonfinite model output")
        _, python_peak = tracemalloc.get_traced_memory()
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        connection.send(
            {
                "status": "ok",
                "parameters": sum(p.numel() for p in model.parameters()),
                "batching_seconds": batching,
                "forward_seconds": durations,
                "median_seconds": statistics.median(durations),
                "p95_seconds": sorted(durations)[math.ceil(len(durations) * 0.95) - 1],
                "observations_per_second": size / statistics.median(durations),
                "process_peak_rss_bytes": rss
                if sys.platform == "darwin"
                else rss * 1024,
                "python_tracemalloc_peak_bytes": python_peak,
                "mps_current_allocated_bytes": torch.mps.current_allocated_memory()
                if device == "mps"
                else None,
                "mps_driver_allocated_bytes": torch.mps.driver_allocated_memory()
                if device == "mps"
                else None,
                "history_records_per_observation": len(observation.history),
                "context_tokens_per_observation": sum(
                    len(e.context) for e in observation.history
                ),
                "candidates_per_observation": len(observation.candidates),
            }
        )
    except Exception as exc:
        connection.send(
            {"status": "failed", "error_type": type(exc).__name__, "error": str(exc)}
        )
    finally:
        connection.close()


def real_samples(
    checkout: Path, seed: int
) -> tuple[int, Observation, Observation, str]:
    mechanics = load_mechanics(checkout)
    raw = json.loads((ROOT / "docs/planning/pokemon/foundation/teams.json").read_text())
    teams = [
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
    with ChampionsBattle(checkout, teams, (seed % 65536, 2, 3, 4)) as battle:
        preview = encode(battle.state.p1, teams[0], mechanics)
        battle.step("team 1234", "team 1234")
        ordinary = encode(battle.state.p1, teams[0], mechanics)
    return len(mechanics.vocabulary), preview, ordinary, mechanics.content_id


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output", type=Path, help="New ignored output directory; never overwritten"
    )
    parser.add_argument(
        "--showdown", type=Path, default=ROOT / "tmp/pokemon-foundation/showdown"
    )
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument(
        "--mps", action="store_true", help="Also measure MPS; CPU always runs"
    )
    args = parser.parse_args()
    reserve_output(args.output)
    vocabulary, preview, ordinary, mechanics_id = real_samples(args.showdown, args.seed)
    config: dict[str, Any] = {
        "schema": "pka038-untrained-probe-v1",
        "trained": False,
        "observation_schema": SCHEMA,
        "seed": args.seed,
        "format": FORMAT,
        "showdown_revision": SHOWDOWN_REVISION,
        "mechanics_id": mechanics_id,
        "python": platform.python_version(),
        "torch": torch.__version__,
        "machine": platform.machine(),
        "platform": platform.platform(),
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "dirty_worktree": bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=ROOT, text=True
            )
        ),
        "processor": platform.processor(),
        "cpu_threads": 1,
        "vocabulary_size": vocabulary,
        "token_width": WIDTH,
        "state_mlp": [256, 256],
        "attention_blocks": 2,
        "attention_heads": 4,
        "attention_feedforward": 256,
        "candidate_parts": PARTS,
        "warmup_passes": WARMUP,
        "timed_passes": PASSES,
        "history_lengths": [16, 64, 256],
        "batch_sizes": [1, 8, 32],
        "devices": ["cpu", "mps"] if args.mps else ["cpu"],
        "memory_scope": "Fresh child peak RSS includes imports/model/input/inference; tracemalloc tracks Python allocations only, excludes native tensors. MPS allocation values are end-of-case snapshots, not peaks. No claim of total system or GPU peak memory.",
        "workload": "Real pinned-engine preview and ordinary menus, with repeated synthetic history records and updated sequence positions. Full records/context preserved. Forward inference only; no learning updates or checkpoint export.",
    }
    with (args.output / "config.json").open("x") as file:
        json.dump(config, file, indent=2)
    context = mp.get_context("spawn")
    results = []
    progress = True
    for device in config["devices"]:
        for kind in ("mlp", "attention"):
            for phase, sample in (("preview", preview), ("ordinary", ordinary)):
                for length in config["history_lengths"]:
                    observation = synthetic_history(sample, length)
                    for size in config["batch_sizes"]:
                        case_id = f"{device}-{kind}-{phase}-h{length}-b{size}"
                        result: dict[str, Any] = {
                            "case": case_id,
                            "device": device,
                            "model": kind,
                            "phase": phase,
                            "history": length,
                            "batch_size": size,
                        }
                        if device == "mps" and not torch.backends.mps.is_available():
                            result.update(
                                status="failed",
                                error="Requested MPS device is unavailable",
                            )
                        else:
                            reader, writer = context.Pipe(duplex=False)
                            process = context.Process(
                                target=_case,
                                args=(
                                    writer,
                                    observation,
                                    vocabulary,
                                    kind,
                                    size,
                                    device,
                                    args.seed,
                                ),
                            )
                            process.start()
                            writer.close()
                            # Read before join so a full pipe cannot deadlock the child.
                            try:
                                if reader.poll(180):
                                    result.update(reader.recv())
                                else:
                                    result.update(
                                        status="failed",
                                        error="Case exceeded 180-second wall limit",
                                    )
                                    process.terminate()
                            except EOFError:
                                result.update(
                                    status="failed",
                                    error="Child exited without a result (possible resource failure)",
                                )
                            finally:
                                reader.close()
                                process.join(timeout=5)
                                if process.is_alive():
                                    process.terminate()
                                    process.join(timeout=5)
                                if process.is_alive():
                                    process.kill()
                                    process.join(timeout=5)
                                if process.is_alive():
                                    raise RuntimeError(
                                        "Cannot release benchmark child process"
                                    )
                            result["exit_code"] = process.exitcode
                            if process.exitcode != 0:
                                result["status"] = "failed"
                        results.append(result)
                        with (args.output / f"{case_id}.json").open("x") as file:
                            json.dump(result, file, indent=2)
                        # Progress is separate from the durable result write.
                        if progress:
                            try:
                                print(f"{case_id}: {result['status']}", flush=True)
                            except BrokenPipeError:
                                progress = False
    with (args.output / "results.json").open("x") as file:
        json.dump(results, file, indent=2)
    if any(result["status"] != "ok" for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
