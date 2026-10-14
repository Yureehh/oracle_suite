"""Champions text imports preserve missing information and reject ambiguity."""

import json
import os
from dataclasses import replace
from pathlib import Path

import pytest
from strixia_agon.pokemon.simulator import TeamMember
from strixia_agon.pokemon.teams import import_team, read_team, validate_team

PASTE = """Friend (Greninja) (M) @ Sitrus Berry
Ability: Torrent
Level: 50
EVs: 2 HP / 32 Atk / 32 Spe
Jolly Nature
- Water Shuriken
- Night Slash
- Protect
- Ice Punch
"""


def test_native_text_and_missing_spreads(tmp_path: Path) -> None:
    imported = import_team(PASTE.replace("\n", "\r\n"))
    member = imported[0]
    assert (member.species, member.nickname, member.gender) == (
        "Greninja",
        "Friend",
        "M",
    )
    complete = member.complete()
    assert complete.stat_points == dict(
        hp=2, atk=32, **{"def": 0}, spa=0, spd=0, spe=32
    )
    partial = import_team(PASTE.replace("EVs: 2 HP / 32 Atk / 32 Spe\n", ""))[0]
    assert partial.stat_points is None
    with pytest.raises(ValueError, match="stat points"):
        partial.complete()
    file = tmp_path / "team.txt"
    file.write_text(PASTE)
    assert read_team(file) == imported


@pytest.mark.parametrize(
    "line",
    [
        "EVs: 252 Atk / 252 Spe",
        "EVs: 0.5 HP",
        "EVs: -1 HP",
        "EVs: 32 HP / 32 Atk / 3 Spe",
        "EVs: 2 HP / 2 HP",
        "EVs: 2 Nope",
    ],
)
def test_bad_allocations(line: str) -> None:
    with pytest.raises(ValueError):
        import_team(PASTE.replace("EVs: 2 HP / 32 Atk / 32 Spe", line))


def test_ambiguous_or_unsupported_input() -> None:
    with pytest.raises(ValueError, match="alternative"):
        import_team(PASTE.replace("- Protect", "- Protect / Detect"))
    with pytest.raises(ValueError, match="Duplicate"):
        import_team(PASTE + "Ability: Torrent\n")
    with pytest.raises(ValueError, match="Unknown"):
        import_team(PASTE + "Mystery: value\n")
    legacy = import_team(PASTE + "Tera Type: Water\n")[0]
    assert legacy.complete()
    assert ("Tera Type", "Water") in legacy.metadata
    assert "Tera Type" not in legacy.complete()._engine_set()
    with pytest.raises(ValueError, match="IV"):
        import_team(PASTE + "IVs: 0 Atk\n")[0].complete()
    with pytest.raises(ValueError, match="PokePaste"):
        read_team("https://example.org/team")


def test_engine_legality() -> None:
    root = Path(__file__).resolve().parents[4]
    checkout = Path(
        os.environ.get(
            "STRIXIA_SHOWDOWN_PATH", root / "tmp/pokemon-foundation/showdown"
        )
    )
    if not (checkout / "dist/sim/index.js").exists():
        pytest.skip("Prepare the pinned engine with prepare.sh --engine-only")
    raw = json.loads((root / "docs/planning/pokemon/foundation/teams.json").read_text())
    teams = [
        [
            TeamMember(
                m["species"], m["ability"], tuple(m["moves"]), m["nature"], m["evs"]
            )
            for m in team
        ]
        for team in raw
    ]
    valid = validate_team(checkout, tuple(teams[0]))
    assert len(valid) == 6
    aliases = tuple(
        replace(m, moves=tuple(move.lower() for move in m.moves)) for m in valid
    )
    assert validate_team(checkout, aliases) == valid
    text = "\n\n".join(
        f"{m.species}\nAbility: {m.ability}\n{m.nature} Nature\n"
        + "EVs: "
        + " / ".join(
            f"{v} {s}"
            for s, v in zip(
                ("HP", "Atk", "Def", "SpA", "SpD", "Spe"),
                m.stat_points.values(),
                strict=True,
            )
        )
        + "\n"
        + "\n".join(f"- {move}" for move in m.moves)
        for m in teams[0]
    )
    assert validate_team(checkout, tuple(m.complete() for m in import_team(text)))
    with pytest.raises(ValueError, match="Species Clause"):
        validate_team(checkout, (valid[0], valid[0], *valid[2:]))
    duplicate_items = tuple(replace(m, item="Sitrus Berry") for m in valid)
    with pytest.raises(ValueError, match="Item Clause"):
        validate_team(checkout, duplicate_items)
    with pytest.raises(ValueError, match="Wonder Guard"):
        validate_team(checkout, (replace(valid[0], ability="Wonder Guard"), *valid[1:]))


def test_bounded_files_and_incomplete_fields(tmp_path: Path) -> None:
    oversized = tmp_path / "large.txt"
    oversized.write_bytes(b"x" * (128 * 1024 + 1))
    with pytest.raises(ValueError, match="128 KiB"):
        read_team(oversized)
    for line in ("Ability: Torrent\n", "Jolly Nature\n"):
        partial = import_team(PASTE.replace(line, ""))[0]
        with pytest.raises(ValueError, match="ability or nature"):
            partial.complete()
    assert import_team(PASTE + "IVs: 31 HP / 31 Atk\n")[0].complete()


@pytest.mark.parametrize(
    "url",
    [
        "http://pokepast.es/0123456789abcdef",
        "https://pokepast.es@localhost/0123456789abcdef",
        "https://pokepast.es/0123456789abcdef?url=http://localhost",
        "https://pokepast.es:1234/0123456789abcdef",
        "https://pokepast.es/not-a-paste",
    ],
)
def test_only_canonical_pokepaste_urls(url: str) -> None:
    with pytest.raises(ValueError, match="PokePaste"):
        read_team(url)


def test_http_body_limit_and_redirect_rejection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import io
    from urllib.request import Request

    from strixia_agon.pokemon import teams

    payload = PASTE.encode()
    url = "https://pokepast.es/0123456789abcdef"

    class ResponseOpener:
        def open(self, target: str, *, timeout: int) -> io.BytesIO:
            assert target == url + "/raw" and timeout > 0
            return io.BytesIO(payload)

    def opener(handler: teams._NoRedirect) -> ResponseOpener:
        with pytest.raises(ValueError, match="redirects"):
            handler.redirect_request(
                Request(url), None, 302, "Found", {}, "http://localhost/"
            )
        return ResponseOpener()

    monkeypatch.setattr(teams, "build_opener", opener)
    assert read_team(url) == import_team(PASTE)
    payload = b"x" * (128 * 1024 + 1)
    with pytest.raises(ValueError, match="128 KiB"):
        read_team(url)
