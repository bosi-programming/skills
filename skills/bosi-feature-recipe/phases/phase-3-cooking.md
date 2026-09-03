# Phase 3 — Cooking

Turn the failing tests into passing code.

## 1. PR delivery strategy, if the plan is big enough

Read the `## Implementation Plan` and estimate the shape of the whole thing:
files touched, lines changed (code + tests), the natural seams (a schema
change, a service layer, an endpoint, a UI, the tests for each).

If the whole plan comes in at roughly 500 lines and 10 files or under, skip
straight to section 2 — one PR, no chunking needed.

Otherwise, group the plan into PR-sized chunks at or under that size, each
with a single clear purpose, each shipping its own tests rather than
"feature now, tests later", each independently reviewable. Present the
chunks, get the user's confirmation or adjust and re-present, then write the
confirmed chunks to `## PR Delivery Strategy`.

If splitting genuinely isn't feasible — an atomic migration, an indivisible
refactor — ask the user to say why, record that justification in
`## PR Delivery Strategy`, and proceed as a single PR anyway.

## 2. Implement, chunk by chunk

Work through the Implementation Plan in the order the delivery strategy
sets. For each step:

1. Say what's about to change.
2. Make the change.
3. Run the tests this step's acceptance criterion maps to (from the
   `## TDD Test Mapping`) and confirm they now pass. If a gap turns up —
   behavior the existing tests don't cover — write a test for it, confirm it
   fails, then close the gap.
4. Commit at each chunk boundary, so each PR chunk can be created
   independently later.
5. At key decisions or after a significant change, pause: summarize what
   happened, flag anything that deviated from the plan, and ask if the user
   wants to look before continuing.

If something comes up the Implementation Plan didn't anticipate, stop and
discuss it with the user before implementing around it. If the plan itself
needs to change, update the relevant recipe-card section rather than quietly
drifting from what it says.

Apply config changes from the Testing/Config sections of the card as they
come up in the plan, and note what was changed.

## 3. Confirm it actually behaves

Once implementation is done, run the app or the affected surface and confirm
the change behaves the way the Acceptance Criteria describe — this is
checking the real thing works, not just that the tests are green.

## 4. Close the phase

Summarize what was implemented against the Implementation Plan. Append one
line to `## Decisions`. Update the frontmatter — `phase: 'cooking'`, append
to `phasesCompleted`, `lastTouched`.

## 5. Phase done

> **Phase done. [N] New session (recommended) — resume next phase fresh. [C] Continue here.**

**N:** confirm the card is saved, tell the user to resume with the same
trigger phrase in a new session. End the session.

**C:** load, read completely, and execute `phase-4-tasting.md`.
