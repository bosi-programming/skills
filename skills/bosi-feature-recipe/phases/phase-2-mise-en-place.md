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

## 2. Confirm nothing's missing with /grill-me

Once every section above is drafted, run `/grill-me` against the whole
recipe card as it now stands — not just the newest section — so a gap
between, say, the Implementation Plan and the Acceptance Criteria surfaces
before code gets written. Don't move on until its frontier is empty.

## 3. Write the failing tests

This is where tests get written, not Cooking — cooking is where they get
made to pass.

1. Explore the codebase's existing test patterns first: find the test
   framework from its config, read a couple of tests near the area this
   task touches, and note the structure, assertion style, and any
   factories/builders in use. Match them exactly.
2. Work through the acceptance criteria one at a time. For each: write the
   test(s) covering its happy path and the edge cases the Testing Strategy
   calls for, then run it and confirm it fails. An import error for
   something that doesn't exist yet is an expected failure; a test that
   passes unexpectedly means the behavior may already exist — stop and
   investigate rather than moving on.
3. If the task is a bug fix, write the regression test first (it must fail,
   proving the bug is real) before the tests defining the fix.

Write the AC → test mapping to the `## TDD Test Mapping` section as you go.

## 4. Close the phase

Append one line to `## Decisions`. Update the frontmatter —
`phase: 'mise-en-place'`, append to `phasesCompleted`, `lastTouched`.

## 5. Phase done

> **Phase done. [N] New chat (recommended) — resume next phase fresh. [C] Continue here.**

**N:** confirm the card is saved, tell the user to resume with the same
trigger phrase in a new session. End the session.

**C:** load, read completely, and execute `phase-3-cooking.md`.
