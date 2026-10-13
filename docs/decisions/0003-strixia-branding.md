# ADR 0003: Strixia identity and local namespace migration

- Status: Accepted
- Date: 2026-10-13
- Supersedes: naming and local package/product paths in ADRs 0001 and 0002 only

## Decision

The owner selected Strixia as the umbrella identity and approved these names:

| Former name | Accepted name | Responsibility |
| --- | --- | --- |
| Oracle | Strixia | Platform |
| Arena | Agon | Competitive intelligence |
| Bets | Pythia | Forecasting and predictive intelligence |
| Lab | Lyceum | Research and experiments |
| Foresight | Theoria | Replay and decision analysis |
| Delphi | Delphi | Matchup exploration and preparation |
| Augur | Metis | Agents and learning |
| Forge | Techne | Team and spread optimization |

Gauntlet is a Delphi matchup-testing feature. The model league and practice/coaching
are Metis features, with shared Theoria/Delphi analysis where needed. They are not
additional product brands. Pair product names with their descriptions in future UI.
Core remains an internal shared-infrastructure name.

The owner approved a full local rename while the packages are still shells:
`oracle-core` / `oracle_core` become `strixia-core` / `strixia_core`, and
`oracle-arena` / `oracle_arena` become `strixia-agon` / `strixia_agon`.
Both distributable packages move to 0.2.0 for incompatible distribution/import names;
there are no compatibility aliases. The non-distributable root becomes
`strixia-workspace` and retains its 0.1.0 metadata version. Pokémon remains inside
`strixia_agon.pokemon`. Product folders become `products/agon/`, `products/pythia/`
and `products/lyceum/`.

## Boundaries and migration

Branding creates no services, libraries, additional training systems or game mechanics.
Agon owns game AI; Lyceum exposes actual producer results. Existing dependency and
information boundaries remain in force.

Update local imports, package metadata, workspace/test/type-check paths, lockfile,
build commands, documentation links and instruction indexes together. Future proposed
environment variables use `STRIXIA_<COMPONENT>_<SETTING>`; no runtime variables exist yet.

The checkout remains `/Users/yureeh/dev/oracle_suite`; the GitHub repository remains
`https://github.com/Yureehh/oracle_suite`. The separately inspected Oracle Bets project,
its filesystem/package identifiers and its history remain unchanged. Historical ADRs,
changelog entries, source names and the algorithm term double-oracle are preserved.

## Alternatives

Branding-only changes would avoid import changes but retain conflicting internal names.
The owner chose the full local rename now because no product runtime consumes these
shells. Striai was considered; Strixia is the accepted spelling.

## Validation and release

Require valid documentation/instruction paths, preserved task identities/dependencies,
the root checks, and isolated installation of both built distributions. Record the
migration under Unreleased. No push, merge, tags, publication or application
implementation is authorized by this naming change.
