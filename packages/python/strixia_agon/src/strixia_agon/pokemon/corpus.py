"""Versioned native teams; spread/move variants share only their split group."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

from .simulator import FORMAT, SHOWDOWN_REVISION, TeamMember
from .teams import team_data


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def make_manifest(
    candidates: Sequence[tuple[tuple[TeamMember, ...], Mapping[str, str]]],
    *,
    source_hash: str,
) -> dict[str, Any]:
    """Deduplicate exact teams; deterministically partition composition groups.

    Callers must engine-validate candidates first. Species grouping does not merge
    spread, move, item, gender, ability or nature variants into one team record.
    """
    unique: dict[str, dict[str, Any]] = {}
    for team, source in candidates:
        if len(team) != 6:
            raise ValueError("Corpus teams require six members")
        members = team_data(team)
        # Slots have no team identity; retain deterministic move order in records.
        for m in members:
            m["moves"] = sorted(m["moves"])
        members.sort(key=_canonical)
        identity = hashlib.sha256(_canonical(members).encode()).hexdigest()
        record = unique.setdefault(
            identity,
            {
                "id": identity,
                "members": members,
                "composition": sorted(m.species for m in team),
                "sources": [],
            },
        )
        if dict(source) not in record["sources"]:
            record["sources"].append(dict(source))
    groups = {_canonical(r["composition"]) for r in unique.values()}
    if len(groups) < 3:
        raise ValueError("Need at least three compositions for train/validation/test")
    ordered = sorted(groups, key=lambda g: hashlib.sha256(g.encode()).hexdigest())
    train_count = min(len(ordered) - 2, max(1, int(len(ordered) * 0.70)))
    validation_count = min(
        len(ordered) - train_count - 1, max(1, int(len(ordered) * 0.15))
    )
    assignments = {
        group: "train"
        if i < train_count
        else "validation"
        if i < train_count + validation_count
        else "test"
        for i, group in enumerate(ordered)
    }
    records = []
    for identity in sorted(unique):
        record = unique[identity]
        record["split"] = assignments[_canonical(record["composition"])]
        record["sources"].sort(key=_canonical)
        records.append(record)
    body = {
        "schema": 1,
        "format": FORMAT,
        "showdown_revision": SHOWDOWN_REVISION,
        "source_hash": source_hash,
        "split_policy": "species-composition-sha256-rank-70-15-15-v1",
        "group_counts": {
            label: sum(v == label for v in assignments.values())
            for label in ("train", "validation", "test")
        },
        "teams": records,
    }
    return {"id": hashlib.sha256(_canonical(body).encode()).hexdigest(), **body}


def source_records(raw: str) -> list[dict[str, str]]:
    rows = list(csv.reader(io.StringIO(raw)))
    if not rows or not any("(Champions M-C)" in cell for cell in rows[0]):
        raise ValueError("Source must identify Champions M-C explicitly")
    header = next(
        (i for i, row in enumerate(rows) if row and row[0] == "Team ID"), None
    )
    if header is None:
        raise ValueError("Missing source Team ID header")
    columns = rows[header]
    labels = (
        "Team ID",
        "Team Description",
        "Pokepaste",
        "EVs",
        "Extracted paste?",
        "Date Shared",
        "Tournament / Event",
        "Rank",
        "Link to Source",
        "Report / Video",
    )
    indices = {label: columns.index(label) for label in labels}
    records = []
    seen = set()
    for row in rows[header + 1 :]:
        if not row or not row[0]:
            continue
        if not re.fullmatch(r"MC[0-9]+", row[0]) or row[0] in seen:
            raise ValueError(f"Unexpected or duplicate M-C source ID: {row[0]}")
        seen.add(row[0])
        record = {
            label: row[index] if index < len(row) else ""
            for label, index in indices.items()
        }
        records.append(record)
    return records
