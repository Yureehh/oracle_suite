# Champions team imports

PKA-021 adds classic Showdown/PokePaste text imports. All runtime input uses Champions
M-C stat points: the historical `EVs:` label contains native integer allocations,
not Scarlet/Violet investment. No legacy conversion is performed.

```bash
uv run --locked --all-packages python scripts/pokemon_teams.py team.txt
uv run --locked --all-packages python scripts/pokemon_teams.py -
uv run --locked --all-packages python scripts/pokemon_teams.py https://pokepast.es/3c5c76e62146a2c5 --validate
```

The first command accepts an incomplete import for inspection. The second reads
standard input. `--validate` requires six complete members and validates against the
pinned engine prepared with the [foundation guide](../planning/pokemon/foundation/README.md).
It outputs both the original imported fields and normalized simulation team JSON.
The normalized member objects can be used with `TeamMember` and the existing
[two-team demonstration](../planning/pokemon/foundation/005-adapter.md).

Missing allocation lines remain unknown. Omitted stats within an explicit allocation
line are zero according to the export syntax. Ability and nature must be explicit
for simulation; no missing field is silently inferred. Nicknames and cosmetic
metadata are preserved in the import; simulation uses normalized species and
abilities, level 50 and the engine's all-31 IV sentinel. Nonmax IVs, move alternatives and incompatible allocations cannot produce a
simulation team. Legacy Tera/Dynamax/Gigantamax annotations are preserved as
explicitly inactive metadata and never forwarded to the Champions engine. Missing spreads are useful for inspection and future viewer work.

Only canonical HTTPS pokepast.es URLs are fetched, with a 15-second timeout, no
redirects and a 128 KiB limit. Local files and stdin have the same size limit.
The module exposes `import_team(text)`, `read_team(path_or_url)`, member `.complete()`
and `validate_team(checkout, team)`. Legal validation returns normalized members;
it does not prove actual-game parity.

Source syntax: [PokePaste](https://pokepast.es/syntax.html),
[pinned Showdown team documentation](https://github.com/smogon/pokemon-showdown/blob/3a766f2cfb5e51c1e428cfe87d0dba91a8f01640/sim/TEAMS.md).
