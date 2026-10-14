"""Import a Champions team from a text file, stdin or a PokePaste URL."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from strixia_agon.pokemon.simulator import SimulatorError
from strixia_agon.pokemon.teams import import_team, read_team, team_data, validate_team

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="Text file, HTTPS PokePaste URL, or - for stdin")
    parser.add_argument(
        "--validate", action="store_true", help="Require complete legal M-C team"
    )
    parser.add_argument(
        "--showdown", type=Path, default=ROOT / "tmp/pokemon-foundation/showdown"
    )
    args = parser.parse_args()
    try:
        if args.source == "-":
            imported = import_team(sys.stdin.read(128 * 1024 + 1))
        else:
            imported = read_team(
                args.source if args.source.startswith("https://") else Path(args.source)
            )
        output: dict[str, object] = {
            "source": args.source,
            "members": [asdict(m) for m in imported],
        }
        if args.validate:
            complete = validate_team(
                args.showdown, tuple(m.complete() for m in imported)
            )
            output["validated_team"] = team_data(complete)
        print(json.dumps(output, indent=2))
    except (ValueError, OSError, SimulatorError) as exc:
        parser.exit(1, f"Team import failed: {exc}\n")


if __name__ == "__main__":
    main()
