"""Immutable versioned ground knowledge exported from the pinned Champions Dex."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .simulator import FORMAT, SHOWDOWN_REVISION, SimulatorError


def identifier(value: str) -> str:
    """Use Showdown's ASCII identifier normalization."""
    return re.sub("[^a-z0-9]", "", value.lower())


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


@dataclass(frozen=True)
class Mechanics:
    revision: str
    content_id: str
    species: Mapping[str, Mapping[str, Any]]
    moves: Mapping[str, Mapping[str, Any]]
    natures: Mapping[str, Mapping[str, str | None]]
    vocabulary: tuple[str, ...]
    indices: Mapping[str, int]

    def category(self, kind: str, value: str | None) -> int:
        """0 is padding, 1 unknown, 2 absent; unknown identities fail explicitly."""
        if value is None:
            return 1
        if not value:
            return 2
        key = f"{kind}:{identifier(value)}"
        try:
            return self.indices[key]
        except KeyError as exc:
            raise ValueError(f"Unsupported mechanics identity {key}") from exc


def load_mechanics(checkout: Path) -> Mechanics:
    """Export static metadata only; no simulator state is requested."""
    try:
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=checkout, text=True
        ).strip()
        if revision != SHOWDOWN_REVISION:
            raise SimulatorError("Expected pinned Showdown revision")
        result = subprocess.run(
            [
                "node",
                str(Path(__file__).with_name("engine_bridge.cjs")),
                str(checkout.resolve()),
            ],
            input='{"op":"mechanics"}\n',
            capture_output=True,
            text=True,
            timeout=15,
            check=True,
        )
        reply = json.loads(result.stdout)
        if not reply["ok"]:
            raise SimulatorError(reply["error"])
        data = reply["frame"]
        if data["format"] != FORMAT:
            raise SimulatorError("Unexpected mechanics format")
    except (OSError, subprocess.SubprocessError, KeyError, json.JSONDecodeError) as exc:
        raise SimulatorError("Cannot export pinned Champions mechanics") from exc
    vocab: set[str] = set()
    for kind in ("species", "moves"):
        vocab.update(
            f"{kind[:-1] if kind == 'moves' else kind}:{m['id']}" for m in data[kind]
        )
    for plural, singular in [
        ("items", "item"),
        ("abilities", "ability"),
        ("natures", "nature"),
        ("types", "type"),
    ]:
        vocab.update(f"{singular}:{identifier(v)}" for v in data[plural])
    effects = (
        set(data["effects"])
        | set(data["items"])
        | set(data["abilities"])
        | {m["id"] for m in data["moves"]}
    )
    vocab.update(f"effect:{identifier(v)}" for v in effects)
    vocab.update(
        f"status:{v}" for v in ("brn", "par", "slp", "psn", "tox", "frz", "fnt")
    )
    vocab.update(f"category:{x}" for x in ("physical", "special", "status"))
    vocab.update(f"flag:{x}" for move in data["moves"] for x in move["flags"])
    vocabulary = ("<pad>", "<unknown>", "<absent>", *sorted(vocab))
    return Mechanics(
        revision,
        hashlib.sha256(
            json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        _freeze({m["id"]: m for m in data["species"]}),
        _freeze({m["id"]: m for m in data["moves"]}),
        _freeze(data["natureModifiers"]),
        vocabulary,
        MappingProxyType({v: i for i, v in enumerate(vocabulary)}),
    )
