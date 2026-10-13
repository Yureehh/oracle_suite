# RL and search learning path

Created: 2026-10-12

The owner is experienced in Python/data science but wants to learn RL through this
project. Before each task explain the concepts below using the current Pokémon case;
do not assume knowledge of jargon or turn this into a separate theory prerequisite.

| Story stage | Concept | Practical meaning |
| --- | --- | --- |
| PKA-001–003 | State and observation | Engine knows everything; a player receives only permitted information and history |
| PKA-006–008 | Action, mask and episode | A coordinated move pair must be legal; battle and Bo3 set have different ending/reset semantics |
| PKA-023–026 | Belief | Weighted possibilities for hidden attributes; observations change weights, not magically reveal truth |
| PKA-027–029 | Value and mixed strategy | A value depends on assumptions; a mixed strategy assigns probabilities to several decisions |
| PKA-030 | Double-oracle | Start with a small action matrix, solve it, find missing counterplay, add actions and solve again |
| PKA-031 | Search depth | Simulate later turns; independent of how many actions the current-turn matrix contains |
| PKA-037–040 | Policy, rollout, reward, advantage | Policy chooses actions; rollout gathers experience; reward defines the target; advantage compares an action's return with a baseline |
| PKA-040–041 | PPO | Reuse collected experience for bounded policy updates; clipping discourages excessive probability changes but is not a universal guarantee |
| PKA-038/043 | Memory and self-play | History informs partial-observation decisions; changing opponents make training nonstationary |
| PKA-042/044 | BC and fine-tuning | BC imitates recoverable demonstrations; fine-tuning starts from learned weights, which can help or hurt a new regulation |
| PKA-032/047 | Calibration and evaluation | Probability meaning requires held-out evidence; winning against one weak opponent does not establish broad competence |
| PKA-045 | Performance | Measure environment, IPC, inference and update time before optimizing a bottleneck |

## Double-oracle example

Suppose a one-turn matrix initially compares two of our coordinated decisions with
two opponent decisions. Solve the 2×2 game for mixed strategies. Now search the omitted
legal actions for a response that performs well against the opponent mixture. Add it
as a row (or an opponent response as a column), then solve the larger matrix. Repeat
within a budget. This expands coverage at the same depth; it does not mean two moves
or two turns ahead. With approximate response searches, global convergence/optimality
is not guaranteed. PKA-030 compares this with simply evaluating more initial actions.

## What the model learns

A policy head suggests how likely different legal joint actions should be. A value
head estimates future outcomes under its training/evaluation setting. Shared features
can represent Pokémon, moves, field conditions and known history. Neither a value head
nor self-play makes predictions calibrated or strategy optimal automatically.

A Champions base model would be our own tested checkpoint, not a generic Pokémon model
we can assume exists. Freeze and version it, then compare regulation fine-tuning with
fresh training. New mechanics, species/actions and different team distributions can
invalidate observations or learned habits. More compute cannot repair leaked data or
an incorrect simulator.

Each implementation discussion should include a small worked example, the relevant
math only when useful, exact input/output behavior, and one test that demonstrates
the idea. Research task reviews must distinguish observations, hypotheses and conclusions.
