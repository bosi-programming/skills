# Phase 2 — Mise en Place

Get everything ready before the cooking starts: the design, and the tests
that prove it.

## 1. Draft the design, section by section

Read the `## Problem` section of the recipe card, then work through the
following with the user, discussing and iterating on each before moving to
the next. Write each to the recipe card as soon as it's approved — don't
hold multiple sections in the air waiting for a final review pass.

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

## 2. Confirm nothing's missing with the `grill-me` skill

Once every section above is drafted, invoke the `grill-me` skill (Skill tool) against the whole
recipe card as it now stands — not just the newest section — so a gap
between, say, the Implementation Plan and the Acceptance Criteria surfaces
before code gets written. Don't move on until its frontier is empty.

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
