# code-visualizer backlog

Data to add to the change model so the page tells a reviewer more than the diff does.
One at a time, in this order.

## 1. Diff hunks on nodes — done

`nodes[].hunks[]`, same shape as `patterns[].evidence[]`. The raw diff used to reach
the page only through a pattern, so a changed file with no pattern was a box nobody
could read. Reuses the evidence view.

Shipped: `normalize_hunks` plus a `warnings()` pass in `render_graph.py`, one
registry with pattern evidence first and hunks after it, `_hunks` mapping a node to
its registry slots, a `Changed lines` column in the strip, and a hunk-aware evidence
header. Tests in `scripts/test_model.py` and `scripts/test_render.js`.

## 2. Test coverage of the change — done

`nodes[].tests` = `{ status: "added" | "existing" | "none", refs: [...], note }`.
Source: test files inside the diff, plus a grep for the changed symbol across
`*.test.*`, `*.spec.*` and `*_test.*`. Answers "which changed file ships with no
test", and keeps `none` distinct from an absent field, which means nobody looked.

Shipped: `normalize_tests` with two shorthands, `untested_count`, a second
`warnings()` nudge, a red `no test` mark on the box and in the file list, an
untested count in the header, a `no test` chip that dims everything covered, and a
`Tests` column in the strip whose refs jump to the test node when it is in the
graph.

## 3. Contract surface changes

Top-level `surface[]` = `{ kind, name, change, breaking, ref }`. `kind` is one of
exported symbol | http route | DB migration | env var | config key | feature flag |
event name | queue topic. Patterns cover design; this covers what breaks for callers.

## 4. Churn and ownership per file

`nodes[].history` = `{ commits_90d, authors_90d, last_change, owners }`. Source:
`git log --since=90.days --format='%an' -- <file>` and CODEOWNERS. Turns "this file
changed" into "this fragile, many-author file changed".

## 5. Reading order

Top-level `reading_order: [node ids]`. The graph shows topology but not where to
start reading. Direct fix for the "I can't follow this diff" trigger.

## 6. Risks and open questions

`risks[]` = `{ severity, statement, ref, question }`. Distinct from patterns: a
missing guard is not a pattern violation but is what a reviewer needs to see.
Renders as a second card list beside patterns.

## Notes

- `layer` is taken by file vs code. An architectural layer field needs another name,
  e.g. `zone`.
- Skipped on purpose: complexity metrics (low payoff), sequence diagrams of the
  runtime path (a second renderer, not a model field).
