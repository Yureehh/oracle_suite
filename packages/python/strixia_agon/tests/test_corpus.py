"""Corpus identity and evaluation partitions are independent of source order."""

from dataclasses import replace
from pathlib import Path

import pytest
from strixia_agon.pokemon.corpus import make_manifest, source_records
from strixia_agon.pokemon.simulator import TeamMember


def team(prefix: str) -> tuple[TeamMember, ...]:
    return tuple(
        TeamMember(
            f"{prefix}{i}",
            "Ability",
            ("Move",),
            "Hardy",
            dict.fromkeys(("hp", "atk", "def", "spa", "spd", "spe"), 0),
        )
        for i in range(6)
    )


def test_variants_are_distinct_and_grouped_duplicates_keep_sources() -> None:
    first = team("A")
    variant = (
        replace(
            first[0], stat_points=dict(hp=1, atk=0, **{"def": 0}, spa=0, spd=0, spe=0)
        ),
        *first[1:],
    )
    candidates = [
        (first, {"id": "one"}),
        (tuple(reversed(first)), {"id": "duplicate"}),
        (variant, {"id": "variant"}),
    ]
    candidates += [(team(f"Group{i}-"), {"id": str(i)}) for i in range(9)]
    result = make_manifest(candidates, source_hash="csv-hash")
    assert len(result["teams"]) == 11
    grouped = [
        t for t in result["teams"] if t["composition"] == [f"A{i}" for i in range(6)]
    ]
    assert len(grouped) == 2 and len({t["split"] for t in grouped}) == 1
    assert sorted(len(t["sources"]) for t in grouped) == [1, 2]
    assert result == make_manifest(list(reversed(candidates)), source_hash="csv-hash")
    assert {t["split"] for t in result["teams"]} == {"train", "validation", "test"}
    assert result["group_counts"] == {"train": 7, "validation": 1, "test": 2}


def test_too_few_compositions_cannot_claim_holdout_evaluation() -> None:
    with pytest.raises(ValueError, match="three"):
        make_manifest([(team("A"), {"id": "one"})], source_hash="source")


def test_source_tab_and_ids_are_explicit() -> None:
    csv = "VGCPastes Repository (Champions M-C)\nTeam ID,Team Description,Pokepaste,EVs,Extracted paste?,Date Shared,Tournament / Event,Rank,Link to Source,Report / Video\nMC1,description,https://pokepast.es/0123456789abcdef,Yes,Owner's,date,event,1,url,video\n"
    records = source_records(csv)
    assert len(records) == 1 and records[0]["Team ID"] == "MC1"
    assert records[0]["Extracted paste?"] == "Owner's"
    with pytest.raises(ValueError, match="M-C"):
        source_records(csv.replace("Champions M-C", "Champions M-B"))
    with pytest.raises(ValueError, match="duplicate"):
        source_records(csv + csv.splitlines()[-1] + "\n")
    with pytest.raises(ValueError, match="header"):
        source_records("VGCPastes Repository (Champions M-C)\n")


def test_corpus_cli_admission_and_frozen_source_rebuild(tmp_path: Path) -> None:
    import csv
    import json
    import os
    import subprocess
    import sys
    import uuid
    from dataclasses import asdict

    from strixia_agon.pokemon.teams import import_team

    root = Path(__file__).resolve().parents[4]
    checkout = Path(
        os.environ.get(
            "STRIXIA_SHOWDOWN_PATH", root / "tmp/pokemon-foundation/showdown"
        )
    )
    if not (checkout / "dist/sim/index.js").exists():
        pytest.skip("Prepare the pinned engine")
    raw = json.loads(
        (root / "docs/planning/pokemon/foundation/teams.json").read_text()
    )[0]
    base = tuple(
        TeamMember(
            m["species"],
            m["ability"],
            tuple(m["moves"]),
            m["nature"],
            m["evs"],
            gender="M",
        )
        for m in raw
    )
    points = dict(base[0].stat_points)
    points.update(hp=3, atk=31)
    samples = [
        base,
        (
            replace(base[0], species="Blastoise", ability="Torrent", moves=("Surf",)),
            *base[1:],
        ),
        (
            replace(
                base[0], species="Milotic", ability="Marvel Scale", moves=("Surf",)
            ),
            *base[1:],
        ),
        tuple(replace(m, moves=tuple(x.lower() for x in m.moves)) for m in base),
        (replace(base[0], stat_points=points), *base[1:]),
        base,
        (replace(base[0], ability="Wonder Guard"), *base[1:]),
    ]
    saved = tmp_path / "imports"
    saved.mkdir()
    for i, members in enumerate(samples, 1):
        text = "\n\n".join(
            f"{m.species} (M)\nAbility: {m.ability}\n{m.nature} Nature\nEVs: "
            + " / ".join(
                f"{m.stat_points[k]} {label}"
                for k, label in zip(
                    ("hp", "atk", "def", "spa", "spd", "spe"),
                    ("HP", "Atk", "Def", "SpA", "SpD", "Spe"),
                    strict=True,
                )
            )
            + "\n"
            + "\n".join(f"- {move}" for move in m.moves)
            for m in members
        )
        (saved / f"MC{i}.json").write_text(
            json.dumps([asdict(m) for m in import_team(text)])
        )
    source = tmp_path / "source.csv"
    with source.open("w") as file:
        writer = csv.writer(file)
        writer.writerow(["VGCPastes Repository (Champions M-C)"])
        writer.writerow(
            [
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
            ]
        )
        for i in range(1, 8):
            writer.writerow(
                [
                    f"MC{i}",
                    "Reviewed fixture",
                    f"https://pokepast.es/{i:016x}",
                    "No" if i == 6 else "Yes",
                    "Owner's",
                    "2026-10-14",
                    "Fixture event",
                    "1",
                    "fixture",
                    "",
                ]
            )
    manifests = []
    for _ in range(2):
        output = root / "tmp" / f"corpus-test-{uuid.uuid4().hex}"
        command = [
            sys.executable,
            str(root / "scripts/pokemon_corpus.py"),
            str(output),
            "--csv",
            str(source),
            "--imports",
            str(saved),
            "--showdown",
            str(checkout),
        ]
        result = subprocess.run(
            command, check=True, capture_output=True, text=True, timeout=30
        )
        summary = json.loads(result.stdout)
        assert summary["accepted_sources"] == 5 and summary["unique_teams"] == 4
        assert summary["excluded"] == {"incomplete-source": 1, "invalid-team": 1}
        inventory = json.loads((output / "inventory.json").read_text())
        assert any("Wonder Guard" in r.get("reason", "") for r in inventory["records"])
        assert all(r["Extracted paste?"] == "Owner's" for r in inventory["records"])
        manifest = (output / "corpus.json").read_bytes()
        manifests.append(manifest)
        assert subprocess.run(command, capture_output=True, timeout=30).returncode != 0
        assert (output / "corpus.json").read_bytes() == manifest
    assert manifests[0] == manifests[1]
