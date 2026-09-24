# Phase 2 — Mise en Place

Get everything ready before the cooking starts: the design, and the tests
that prove it.

## 1. Draft the design, section by section

Read the `## Problem` section of the recipe card, then draft all five
sections below in one pass — don't stop between them for approval. Present
the whole design as one document and take one round of feedback; go back
only to the sections the user actually flags, not the whole set. Write the
approved version to the recipe card.

- **Solution** — the overall approach, the key design decisions, how it fits
  the existing system.
- **Implementation Plan** — the concrete steps: files/modules to touch, the
  order, the integration points.
- **Acceptance Criteria** — specific, testable, covering the happy path and
  the edge cases from Phase 1.
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

This is where test cases get decided, not written — Cooking is where they
get written (and made to pass). No code, no test-framework exploration here;
that happens in Cooking, right before the real tests get written.

1. Work through the acceptance criteria one at a time. For each, list the
   test case(s) covering its happy path and the edge cases the Testing
   Strategy calls for — a short name and a one-line description per case.
2. If the task is a bug fix, list the regression case first (it proves the
   bug is real) before the cases defining the fix.
3. Present the full case list to the user, iterate until approved.

Write the approved AC → test-case list to the `## TDD Test Mapping` section,
each case marked not yet written.

## 4. Close the phase

Append one line to `## Decisions`. Update the frontmatter —
`phase: 'mise-en-place'`, append to `phasesCompleted`, `lastTouched`.

## 5. Phase done

> **Phase done. [N] New session (recommended) — resume next phase fresh. [C] Continue here.**

**N:** confirm the card is saved, tell the user to resume with the same
trigger phrase in a new session. End the session.

**C:** load, read completely, and execute `phase-3-cooking.md`.

## Headless

Read `../references/headless.md`. In a headless run:

- Set `runNext: phase-2-mise-en-place.md` as you start.
- Section 1's sections are drafted and written straight to the card without
  waiting for approval — take the strongest design judgment, not a
  placeholder, and log each as `unattended:` in `## Decisions`.
- Section 2's cross-check question is answered by the run itself: fix any
  gap it finds and log the fix, or log "no gap found."
- Section 3's test cases are drafted and written to `## TDD Test Mapping`
  without presenting them for approval; log the case count per acceptance
  criterion to `## Decisions`.
- Section 4 is unchanged — the frontmatter is updated either way.
- Section 5 does not apply. This phase does not stop at its own boundary: it
  loads, reads completely and executes `phase-3-cooking.md`, and the run
  continues through Cooking, Tasting, Plating and Documentation. A run stops
  at the recipe's end or at a one-way door, never at a phase boundary.

### Ending a run

Only if this phase is where the run stops — a design decision with no
reasonable default: the ticket leaves the approach genuinely ambiguous, or a
prerequisite fact no tool in this session can find.

1. Set `runStatus: blocked` and `runQuestion` to the id of the entry you
   wrote in `## Open Questions`. Leave `runNext` as this phase: that is what
   a resume re-runs.
2. Log the stop to `## Decisions`.
