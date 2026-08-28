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

## 3. Contract surface changes — done

Top-level `surface[]` = `{ kind, name, change, breaking, ref, note }`. `kind` is
free text over a known list: exported symbol | http route | db migration | env var
| config key | feature flag | event name | queue topic | cli flag. Patterns cover
design; this covers what the change asks of callers.

Shipped: `normalize_surface` (`change` is checked, `kind` is not, `ref` required),
`breaking_count`, a `Contract surface` section in the side panel that narrows with
the selection the way the pattern cards do, a red left border and `breaking` marker
on the breaking rows, a breaking count in the header, a `Breaks for callers` column
in the overview strip, refs that jump to the node when the file is in the graph,
and a `#surface=<index>` deep link. An absent `surface` key is nudged; `[]` is a
real answer.

## 4. Churn and ownership per file — done

`nodes[].history` = `{ commits_90d, authors_90d, last_change, owners, hotspot, note }`.
Source: `git log --since=90.days --format='%an' <base> -- <file>` and CODEOWNERS.
Turns "this file changed" into "this much-touched file changed".

Shipped: `normalize_history` (counts must be counts, owners a list), `hotspot_count`,
an amber `hot` mark on the box beside the red `no test` one, a hotspot count in the
header, a `History` column in the strip that reads as a sentence, and one warning
when no node carries history at all. `hotspot` is the model author's judgment
rather than a threshold the renderer computes.

## 5. Reading order — done

Top-level `reading_order` = `[{ node, why }]`, a bare id also accepted. The graph
shows topology but not where to start reading. Direct fix for the "I can't follow
this diff" trigger.

Shipped: `normalize_reading_order` (unknown node and duplicate both fail),
`step_index`, a numbered prefix on the ordered boxes in accent blue, a
`Read in this order` card in the side panel, `Start here` in the overview strip,
`step 3 of 7` in the selected node's meta line, `n` and `p` to walk the order, and
two warnings: no order at all, and an order that leaves a changed file out.

## 6. Risks and open questions — done

`risks[]` = `{ severity, statement, ref, question, node }`. Distinct from
patterns: a missing guard is not a pattern violation but is what a reviewer needs
to see.

Shipped: `normalize_risks` (`statement` and `ref` required, severity defaults to
medium and an unknown one fails), `high_risk_count`, a `Risks and questions`
section of collapsed cards that narrows with the selection, a red or amber left
border by severity, a risk count in the header, an `Ask the author` column in the
overview strip carrying the high-severity questions, a `Risks` column in the
strip for the selected node, and a `#risk=<index>` deep link. An absent `risks`
key is nudged; `[]` is a real answer.

All six done. The model now carries, per change: the diff itself, its test
coverage, its churn and owners, the contract it moves, the order to read it in,
and the questions to ask about it.

## Notes

- `layer` is taken by file vs code. An architectural layer field needs another name,
  e.g. `zone`.
- Skipped on purpose: complexity metrics (low payoff), sequence diagrams of the
  runtime path (a second renderer, not a model field).
