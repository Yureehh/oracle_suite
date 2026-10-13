# Documentation practices

`products/` owns canonical product definitions. `docs/architecture/` records component
relationships, `docs/decisions/` records consequential choices, and conventions/runbooks
explain engineering practice and executable workflows. Package and application READMEs
explain their own ownership and link to those sources instead of copying specifications.

Label implemented, planned and provisional functionality explicitly. Update docs with
behavior and command changes. Include exact commands from the repository root and
state prerequisites; never invent a clone URL, benchmark, deployment or passing test.
Keep Markdown links relative within the repository and check their targets exist.
Use sequential ADR numbers and preserve old records when superseded.

Scoped instructions add domain constraints without repeating root rules. Root tasks
must explicitly read relevant nested instructions: instruction discovery is dependent
on working directory. See root `AGENTS.md` and its official guidance link.

Record changes under Unreleased. Publishing, licensing and remote setup require owner
authorization. A local changelog entry does not imply a public release.
