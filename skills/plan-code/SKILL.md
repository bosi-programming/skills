---
name: plan-code
description: Plan the code for a ticket — draft Solution, Implementation Plan, Acceptance Criteria, Testing Strategy and Config changes, list the test cases, and name the interfaces on the work card. The second build stage. Runs alone on a work card, or with no card finds or makes one. Use when someone wants the design and test cases for a ticket settled before any code, or this stage redone on a card.
---

# plan-code

Get everything ready before the code gets written: the design, the tests that
prove it, and the names both test and code are written to.

`feature-recipe` and `recipe-relay` run this stage through this skill, and it
also runs alone.

## Input

The path to a work card, the markdown file that carries a task from one stage
to the next. Its shape is `../feature-recipe/references/recipe-card-template.md`.

With no card, load, read completely and execute
`../feature-recipe/phases/phase-0-start.md`. It finds the card for the task or
makes one, then routes back here. A card with an empty `## Problem` has not
been through `evaluate-ticket`: Phase 0 routes it there first.

## Output

The same work card, with this stage's parts written:

- `## Solution` — the approach, with any config changes.
- `## Implementation Plan` — the steps.
- `## Acceptance Criteria` — testable, with the edge cases.
- `## Testing Strategy` — what gets tested and how.
- `## TDD Test Mapping` — the test cases, each marked not yet written.
- `## Interfaces` — the public names both writers code to.
- `## Decisions` — one line for the stage.
- `## Open Questions` — any gap nothing could settle.
- Frontmatter — `phase` set to `plan-code`, `plan-code` appended to
  `phasesCompleted` once, `lastTouched` updated.

## 1. Draft the design, section by section

Read the `## Problem` section of the work card, then draft all five
sections below in one pass — don't stop between them for approval. Present
the whole design as one document and take one round of feedback; go back
only to the sections the user actually flags, not the whole set. Write the
approved version to the work card.

- **Solution** — the overall approach, the key design decisions, how it fits
  the existing system.
- **Implementation Plan** — the concrete steps: files/modules to touch, the
  order, the integration points.
- **Acceptance Criteria** — specific, testable, covering the happy path and
  the edge cases from `## Problem`.
- **Testing Strategy** — what gets tested and how, mapped to each acceptance
  criterion.
- **Config changes** — anything to add, change, or remove; write "none
  required" if there's nothing here rather than leaving it blank.

## 2. Cross-check the card

Once every section above is drafted, ask one closing question rather than
running `grill-me` over the design: does the Implementation Plan cover every
Acceptance Criterion, and does the Testing Strategy map to both? The
section-by-section drafting in step 1 already caught most gaps as they were
written — this is a single check, not another full-tree interrogation. Get
the user's answer, fix what it turns up, and move on.

## 3. List the test cases

This is where test cases get decided, not written — `test` is where they
get written, and `code` makes them pass. No code, no test-framework exploration here;
that happens in `test`, right before the real tests get written.

1. Work through the acceptance criteria one at a time. For each, list the
   test case(s) covering its happy path and the edge cases the Testing
   Strategy calls for — a short name and a one-line description per case.
2. If the task is a bug fix, list the regression case first (it proves the
   bug is real) before the cases defining the fix.
3. Present the full case list to the user, iterate until approved.

Write the approved AC → test-case list to the `## TDD Test Mapping` section,
each case marked not yet written.

## 4. Write the interfaces

Read the card's Solution, Implementation Plan and `## TDD Test Mapping`, then
write the `## Interfaces` section. For each repo the plan touches, list the
public names, their signatures or shapes, and the files they live in. Make it
precise enough that a test writer and a code writer can each code to it
alone, without seeing the other's work.

A plan too vague to name them stops the stage: write the gap to
`## Open Questions` and set `runStatus: needs-input`.

## 5. Close the stage

Append one line to `## Decisions`. Update the frontmatter —
`phase: 'plan-code'`, append `plan-code` to `phasesCompleted` (once, even on a
redo), `lastTouched`.

## 6. Stage done

> **Stage done. [N] New session (recommended) — resume the next stage fresh. [C] Continue here.**

**N:** confirm the card is saved, tell the user to resume with the same
trigger phrase in a new session. End the session.

**C:** load, read completely, and execute
`../test/SKILL.md`.

## Headless

`../feature-recipe/references/headless.md` holds the rules for a headless run.
Read it. In a headless run:

- Set `runNext: plan-code` as you start.
- Section 1's sections are drafted and written straight to the card without
  waiting for approval — take the strongest design judgment, not a
  placeholder, and log each as `unattended:` in `## Decisions`.
- Section 2's cross-check question is answered by the run itself: fix any
  gap it finds and log the fix, or log "no gap found."
- Section 3's test cases are drafted and written to `## TDD Test Mapping`
  without presenting them for approval; log the case count per acceptance
  criterion to `## Decisions`.
- Section 4's `## Interfaces` is written straight to the card; log it
  `unattended:`.
- Section 5 is unchanged — the frontmatter is updated either way.
- Section 6 does not apply. This stage does not stop at its own boundary: it
  loads, reads completely and executes
  `../test/SKILL.md`, and the run continues
  through `test`, `code`, `prepare-pr` and Documentation. A run stops at the
  recipe's end or at a one-way door, never at a stage boundary.

### Ending a run

Only if this stage is where the run stops — a design decision with no
reasonable default: the ticket leaves the approach genuinely ambiguous, a
prerequisite fact no tool in this session can find, or a plan too vague for
section 4 to name its interfaces.

1. Set `runStatus: blocked` (or `runStatus: needs-input` for the section 4
   stop) and `runQuestion` to the id of the entry you wrote in
   `## Open Questions`. Leave `runNext` as `plan-code`: that is what a resume
   re-runs.
2. Log the stop to `## Decisions`.
