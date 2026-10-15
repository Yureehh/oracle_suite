"""Freeze a reviewed-source M-C team corpus for local research, never training."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Any
from urllib.request import urlopen

from strixia_agon.pokemon.corpus import make_manifest, source_records
from strixia_agon.pokemon.teams import ImportedMember, read_team, validate_team

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "https://docs.google.com/spreadsheets/d/1axlwmzPA49rYkqXh7zHvAtSP-TKbM0ijGYBPRflLSWw/export?format=csv&gid=2001945654"
MAX_SOURCE_BYTES = 4 * 1024 * 1024


def fetch_record(
    record: dict[str, str],
    *,
    saved_imports: Path | None = None,
) -> tuple[dict[str, str], tuple[ImportedMember, ...] | None]:
    record = dict(record)
    if record["EVs"] != "Yes":
        record.update(
            status="incomplete-source", reason="Source does not claim supplied spreads"
        )
        return record, None
    try:
        if saved_imports is None:
            imported = read_team(record["Pokepaste"])
        else:
            with (saved_imports / f"{record['Team ID']}.json").open("rb") as file:
                saved = file.read(MAX_SOURCE_BYTES + 1)
            if len(saved) > MAX_SOURCE_BYTES:
                raise ValueError("Saved import exceeds 4 MiB")
            members = json.loads(saved)
            imported = tuple(
                ImportedMember(
                    **(
                        m
                        | {
                            "stat_points": tuple(
                                tuple(point) for point in m["stat_points"]
                            )
                            if m["stat_points"] is not None
                            else None,
                            "moves": tuple(m["moves"]),
                            "metadata": tuple(tuple(field) for field in m["metadata"]),
                        }
                    )
                )
                for m in members
            )
        record["import_hash"] = hashlib.sha256(
            json.dumps(
                [asdict(m) for m in imported],
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        record["status"] = "imported"
        return record, imported
    except (ValueError, OSError, TypeError, KeyError) as exc:
        record.update(status="import-failed", reason=str(exc))
        return record, None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output", type=Path, help="New directory under ignored runtime storage"
    )
    parser.add_argument(
        "--csv", type=Path, help="Reuse a captured source CSV instead of downloading"
    )
    parser.add_argument(
        "--imports",
        type=Path,
        help="Reuse a captured imports directory without network paste requests",
    )
    parser.add_argument(
        "--showdown", type=Path, default=ROOT / "tmp/pokemon-foundation/showdown"
    )
    args = parser.parse_args()
    # Do not accidentally turn public source data into tracked product assets.
    ignored = (
        subprocess.run(
            ["git", "check-ignore", "-q", str(args.output.resolve())], cwd=ROOT
        ).returncode
        == 0
    )
    if not ignored:
        parser.error(
            "Use an ignored output directory, for example tmp/team-corpus/2026-10-14"
        )
    if args.csv:
        with args.csv.open("rb") as file:
            data = file.read(MAX_SOURCE_BYTES + 1)
    else:
        with urlopen(SOURCE, timeout=30) as response:
            data = response.read(MAX_SOURCE_BYTES + 1)
    if len(data) > MAX_SOURCE_BYTES:
        parser.error("Source CSV exceeds 4 MiB")
    records = source_records(data.decode("utf-8"))
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "source.csv").open("xb") as file:
        file.write(data)
    (args.output / "imports").mkdir()
    inventory = []
    candidates = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for index, (record, imported) in enumerate(
            pool.map(partial(fetch_record, saved_imports=args.imports), records), 1
        ):
            if imported is not None:
                with (args.output / "imports" / f"{record['Team ID']}.json").open(
                    "x"
                ) as file:
                    json.dump([asdict(m) for m in imported], file, indent=2)
                    file.write("\n")
                try:
                    normalized = validate_team(
                        args.showdown, tuple(m.complete() for m in imported)
                    )
                    record["status"] = "accepted"
                    candidates.append((normalized, record))
                except ValueError as exc:
                    record.update(status="invalid-team", reason=str(exc))
            inventory.append(record)
            if index % 50 == 0 or index == len(records):
                try:
                    print(
                        f"Inspected {index}/{len(records)}; accepted {len(candidates)} source entries",
                        file=sys.stderr,
                    )
                except BrokenPipeError:
                    pass
    source_hash = hashlib.sha256(data).hexdigest()
    details: dict[str, Any] = {
        "captured_at": datetime.now(UTC).isoformat(),
        "source": SOURCE,
        "source_hash": source_hash,
        "records": inventory,
        "usage_terms": "No explicit redistribution license established; local research snapshot only.",
        "pick_four": {
            "source": "https://pickfour.win/meta",
            "method": "https://pickfour.win/method",
            "role": "M-C tournament discovery and coverage reference; generated spreads are excluded.",
        },
    }
    with (args.output / "inventory.json").open("x") as file:
        json.dump(details, file, indent=2)
        file.write("\n")
    manifest = make_manifest(candidates, source_hash=source_hash)
    with (args.output / "corpus.json").open("x") as file:
        json.dump(manifest, file, indent=2)
        file.write("\n")
    summary = {
        "corpus": manifest["id"],
        "source_rows": len(records),
        "accepted_sources": len(candidates),
        "unique_teams": len(manifest["teams"]),
        "composition_groups": manifest["group_counts"],
        "excluded": {
            s: sum(r["status"] == s for r in inventory)
            for s in sorted({r["status"] for r in inventory})
            if s != "accepted"
        },
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
