# Oracle — Pokémon Arena planning

Created: 2026-10-12

This directory is the persistent repository-local Kanban requested by the owner.
The [board](kanban.md) is authoritative for status, priority and dependency IDs.
The twelve epic files contain 62 product/workflow stories; PKA-000 tracks delivery
of this planning work. The [product brief](../../../products/arena/pokemon/README.md)
is authoritative for product requirements. [Roadmap](roadmap.md) defines sequencing,
[research](research.md) records technical options, and [learning](learning.md) explains
concepts. These are different responsibilities, not competing backlogs.

No GitHub board was created: the repository has no remote and the previously checked
CLI token lacked Projects access. Source-controlled Markdown is the selected fallback.
Files are currently uncommitted; the board survives chats on disk but becomes protected
by Git history only after an explicitly authorized commit. Do not claim a remote backup.

## Start here

Do not read the entire planning folder before each task.

1. Open [the Kanban](kanban.md): it answers what is next and what state work is in.
2. Follow one story link to its epic card: it answers what to build and how to verify it.
3. Read only the research/learning sections needed for that story, then discuss its design.

An epic groups related stories around a larger outcome. For example, E02 groups
simulator integration, legal actions, baseline agents and Bo3 execution. The board
lists those individual stories by status; the epic file holds their scope and acceptance.
It is one backlog viewed in two ways, not two independent task lists.

Start with PKA-004's initial Git snapshot/branch setup, then PKA-001's simulator
compatibility probe. The commit/version policy is in
[CONTRIBUTING.md](../../../CONTRIBUTING.md#commits-and-versions); do not duplicate it here.

## Workflow

| Status | Meaning |
| --- | --- |
| Backlog | Scope captured; not selected or approved |
| Ready for Discussion | A candidate for design/research discussion |
| Ready for Approval | Exact scope, files, dependencies, risks and acceptance agreed |
| In Progress | Owner explicitly authorized this task's implementation |
| In Review | Work verified; waiting for owner review |
| Done | Owner explicitly accepted the implemented and tested result |
| Blocked | Concrete unresolved dependency prevents approved work |

Missing prerequisites alone do not turn every future card into Blocked. Keep future
work in Backlog and identify dependency IDs. Move a single card to Ready for Approval
only after its design is concrete; approval of this backlog is not approval of code.
Never automatically mark In Review as Done or start a related task.

Before implementation present why now, behavior, technical design, alternatives,
exact affected files, dependencies/risks, acceptance checks and learning concepts.
After implementation record actual changes, commands/results, artifacts, commit/PR
references if any and known limits in its epic card; update the board to In Review.
Wait for the owner to accept or request corrections. Preserve review outcomes and
superseded scope instead of erasing history. Status/priority/dependency edits belong
only in the board; card prose references that index rather than duplicating state.

At session start read root/domain instructions, board, selected card and relevant
product/research documents; inspect actual code and Git state. No artifact or package
listed in a story is evidence it exists. Update ideas as evidence changes and record
material decisions in ADRs. Large/refine cards must split into small reviewable stories
before approval; append new IDs and preserve their parent as a scope record.

## Branch workflow

- `main`: accepted release-quality integration points.
- `dev`: accepted development integration; not a dumping ground for unreviewed work.
- `feat/pka-001-short-description`, `fix/pka-...`, or `docs/pka-...`: one selected task,
  branched from dev once history and dev actually exist; proposed PR target is dev.
- Keep implementation on the task branch through review. Owner acceptance plus
  passing checks precedes integration; local commits within an approved task follow the
  contribution policy. Acceptance does not itself authorize a merge, push or release.
- Promote a reviewed release from dev to main through an explicitly authorized PR.
  Do not merge main-only work into dev accidentally or rewrite shared history.

Today Git is unborn main with untracked scaffold files. PKA-004 defines bootstrap
inclusion, initial-history commit, dev creation, remote owner and branch protections.
These cannot honestly be configured as active branch protection without a remote.
Do not stage unrelated files. Initial snapshot/setup remains a separate approval;
subsequent local task commits follow the owner-authorized contribution policy.

## Story conventions

Every card has stable ID, title, actor/outcome, domain, board-indexed status/priority/
size/dependencies, proposed approach, likely components, acceptance, validation,
learning, decisions/risks and implementation/review evidence. S/M are relative scope
estimates, not delivery dates. P0/P1 do not imply immediate authorization.

All implementation cards inherit typed code, applicable scoped instructions,
meaningful behavior/failure tests, applicable lint/type/build checks, reproducibility,
no secret/data leakage, and no unrelated changes. Research cards require actual
versioned measurements and distinguish author claims from reproduced results.
Use the smallest code that meets quality and performance requirements; optimizing
for fewer dollars cannot excuse incorrect simulation or poor evaluation.

If moving later to GitHub Projects, agree which system is authoritative first.
Retire or clearly demote this status index; do not introduce silent bidirectional sync.
