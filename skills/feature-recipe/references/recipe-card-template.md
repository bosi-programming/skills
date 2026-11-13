# Recipe card template

One file per task, at `{cardRoot}/{task-slug}.md`, where `{cardRoot}` is
`feature-recipe.cardsDir` from the settings file, `./recipes` by default.
`{task-slug}` is a kebab-case
short form of the task name or issue reference — `ABC-123` becomes
`abc-123`, "add CSV export" becomes `add-csv-export`.

Copy this whole skeleton when creating a fresh card. Each phase writes only
its own section, below, and never rewrites a section a previous phase wrote.

```markdown
---
task: '<short name or issue reference, whatever the user gave>'
phase: ''                    # last completed phase, e.g. 'plan-code' — a phase
                             # that stopped to ask a question is not completed
phasesCompleted: []
status: 'in-progress'        # delivery status: in-progress | pr-created | delivered
prUrl: ''
runMode: 'interactive'       # interactive | headless — a headless run records itself here
runStatus: ''                # what the last run did: running | terminal | needs-input | blocked | gate
runNext: ''                  # the phase file or stage skill in flight, or none when the recipe is finished
runQuestion: ''              # the id in ## Open Questions that stopped the run
lastTouched: '<date>'
---

## Decisions

<!-- one or two lines per phase, appended as phases complete, never rewritten.
     A headless run prefixes anything it decided alone with `unattended:`. -->

## Open Questions

<!-- written by any phase that reaches a checkpoint nobody in-process can answer.
     One entry per question, which the routing line refers to by its id, and which
     names the phase that asked so a resume routes back to it:
       - q1 — <phase>: <question> — options: <a | b> — recommendation: <the phase's pick> — answer: <empty until answered> -->

## Problem

<!-- written by Phase 1: evaluate-ticket -->

## Goal & measure

<!-- written by Phase 1: evaluate-ticket. What changes for whom, where we
     see it, and what to watch after release — or one `No product metric:`
     line with the indirect benefit and how to check it. -->

## Solution

<!-- written by Phase 2: plan-code -->

## Implementation Plan

<!-- written by Phase 2: plan-code -->

## Acceptance Criteria

<!-- written by Phase 2: plan-code -->

## Testing Strategy

<!-- written by Phase 2: plan-code -->

## TDD Test Mapping

<!-- written by Phase 2: plan-code (test case list); updated by test as each case's test is written, and by code for a gap it finds -->

## Interfaces

<!-- written by Phase 2: plan-code -->

## PR Delivery Strategy

<!-- written by Phase 5: prepare-pr, only if the plan is large enough to warrant chunking.
     Each chunk carries a status — pending / opened / merged — updated by
     prepare-pr across its (possibly multiple) runs for this card. -->

## Quality Gate Results

<!-- written by code -->

## Signals

<!-- written by the stage that raises a signal, one per line: <signal> — <stage> — <evidence>, e.g. no-screen-change — code — only scripts changed -->

## PR

<!-- written by Phase 5: prepare-pr. Appended to, not overwritten — a single PR
     delivery gets one entry; a chunked delivery gets one entry per chunk. -->

## Follow-ups

<!-- written by follow-ups: one line per item a run left open,
     - <kind> <ref> — <ticket> <url> — <opened | matched>, or
     - none — no open items on the card. Rewritten whole on a rerun. -->
```

The `phase` and `phasesCompleted` fields are the only things Phase 0 reads to
route a resumed task to the right phase file — keep them accurate on every
write. Valid phase tokens, in order: `evaluate-ticket`, `plan-code`,
`test`, `code`, `prepare-pr`, `code-docs`. Older cards may hold
`reading-the-recipe`, `mise-en-place`, `cooking`, `tasting`, `plating` and
`documentation`; Phase 0 reads them as `evaluate-ticket`, `plan-code`, a
`code` still to run, a `code` done, `prepare-pr` and `code-docs`.

`runMode` is written when a run starts, not by every phase: Phase 0 sets
`headless` when the invocation asks for it, and an interactive invocation
against a headless card sets it back. It is what a phase resumed in a fresh
context reads to know not to wait on a person.

A headless run carries its handoff in the frontmatter, never in what it prints —
prose gets fenced, glued to a heading, or turned into a question, and a driver
that reads the last line of a turn will miss it. `runStatus`, `runNext` and
`runQuestion` are that handoff; the phase that ends a run writes them, and every
phase sets `runNext` to its own file as it starts. The rules are in
`./headless.md`, next to this file.
