# Recipe card template

One file per task, at `./recipes/{task-slug}.md`. `{task-slug}` is a kebab-case
short form of the task name or issue reference — `ABC-123` becomes
`abc-123`, "add CSV export" becomes `add-csv-export`.

Copy this whole skeleton when creating a fresh card. Each phase writes only
its own section, below, and never rewrites a section a previous phase wrote.

```markdown
---
task: '<short name or issue reference, whatever the user gave>'
phase: ''                    # last completed phase, e.g. 'mise-en-place' — a phase
                             # that stopped to ask a question is not completed
phasesCompleted: []
status: 'in-progress'        # in-progress | pr-created | needs-input | blocked | delivered
prUrl: ''
runMode: 'interactive'       # interactive | headless — a headless run records itself here
lastTouched: '<date>'
---

## Decisions

<!-- one or two lines per phase, appended as phases complete, never rewritten.
     A headless run prefixes anything it decided alone with `unattended:`. -->

## Open Questions

<!-- written by any phase that reaches a checkpoint nobody in-process can answer,
     and by Phase 0 when a headless run starts before Mise en Place.
     One entry per question, which the routing line refers to by its id, and which
     names the phase that asked so a resume routes back to it:
       - q1 — <phase>: <question> — options: <a | b> — recommendation: <the phase's pick> — answer: <empty until answered> -->

## Problem

<!-- written by Phase 1: Reading the Recipe -->

## Solution

<!-- written by Phase 2: Mise en Place -->

## Implementation Plan

<!-- written by Phase 2: Mise en Place -->

## Acceptance Criteria

<!-- written by Phase 2: Mise en Place -->

## Testing Strategy

<!-- written by Phase 2: Mise en Place -->

## TDD Test Mapping

<!-- written by Phase 2: Mise en Place (test case list); updated by Phase 3: Cooking as each case's test is written -->

## PR Delivery Strategy

<!-- written by Phase 5: Plating, only if the plan is large enough to warrant chunking.
     Each chunk carries a status — pending / opened / merged — updated by
     Plating across its (possibly multiple) runs for this card. -->

## Quality Gate Results

<!-- written by Phase 4: Tasting -->

## PR

<!-- written by Phase 5: Plating. Appended to, not overwritten — a single PR
     delivery gets one entry; a chunked delivery gets one entry per chunk. -->
```

The `phase` and `phasesCompleted` fields are the only things Phase 0 reads to
route a resumed task to the right phase file — keep them accurate on every
write. Valid phase tokens, in order: `reading-the-recipe`, `mise-en-place`,
`cooking`, `tasting`, `plating`, `documentation`.

`runMode` is written when a run starts, not by every phase: Phase 0 sets
`headless` when the invocation asks for it, and an interactive invocation
against a headless card sets it back. It is what a phase resumed in a fresh
context reads to know not to wait on a person.

A headless run ends with one routing line — `RECIPE phase=… status=… next=…
card=…` — so the driver can route without parsing prose. It is part of the turn,
not part of the card: don't store it here. The grammar, the statuses and the
checkpoint protocol are in `./headless.md`, next to this file.
