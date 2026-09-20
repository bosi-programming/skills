# Phase 3 — Cooking

Turn the listed test cases into passing code. This phase and Tasting run
back-to-back without stopping for user input — recommend the user switch to
auto-accept-edits mode if they haven't already, then continue regardless of
their answer.

## 1. Implement, step by step

Work through the Implementation Plan one step at a time. For each step:

1. Say what's about to change.
2. Write the test(s) this step maps to (from `## TDD Test Mapping`) and run
   them to confirm they fail. An import error for something that doesn't
   exist yet is an expected failure; a test that passes unexpectedly means
   the behavior may already exist — stop and investigate rather than moving
   on. For a bug fix, write the regression case first.
3. Make the implementation change.
4. Run those tests again and confirm they now pass. If a gap turns up —
   behavior the existing tests don't cover — write a test for it, confirm it
   fails, then close the gap. Mark each case's test as written in
   `## TDD Test Mapping`.
5. Commit.
6. If anything deviated from the plan or needed a judgement call, append it
   to a running decisions log — don't stop, keep implementing. If the plan
   itself needs to change, update the relevant recipe-card section rather
   than quietly drifting from what it says.

Apply config changes from the Testing/Config sections of the card as they
come up in the plan, and note what was changed.

## 2. Confirm it actually behaves

Once implementation is done, run the app or the affected surface and confirm
the change behaves the way the Acceptance Criteria describe — this is
checking the real thing works, not just that the tests are green.

## 3. Check in once, with everything

If the decisions log from section 1 has entries, present it to the user in
one message, get their input, and apply anything they flag. If the log is
empty, don't wait for a reply — note "no deviations" and fall straight
through to closing the phase.

## 4. Close the phase

Summarize what was implemented against the Implementation Plan. Append one
line to `## Decisions`. Update the frontmatter — `phase: 'cooking'`, append
to `phasesCompleted`, `lastTouched`.

## 5. Phase done

Unlike every other phase, this one doesn't offer the New session / Continue
menu — Cooking and Tasting run back-to-back without user input. Load, read
completely, and execute `phase-4-tasting.md` directly.

## Headless

Read `../references/headless.md`. In a headless run:

- Section 3's check-in is taken, not asked: take the recommendation, log it to
  `## Decisions` prefixed `unattended:`, and keep going.
- Section 4 is unchanged — the frontmatter is updated either way.
- Section 5 does not apply in the sense it reads here. Cooking does not stop and
  does not wait to be told to carry on: it loads, reads completely and executes
  `phase-4-tasting.md`, and the run continues through Tasting, Plating and
  Documentation. A run stops at the recipe's end or at a one-way door, never at
  a phase boundary.

Only if this phase is where the run stops does the turn's last line become:

```
RECIPE phase=cooking status=needs-input next=phase-3-cooking.md card=<path> question=<id>
```

### Ending a headless turn

Only the phase that ends the run writes this.

1. Put the outcome on the card: the phase's own section, and `## Open Questions`
   when the run stopped at a one-way door.
2. Make the routing line the last line of the turn, bare, with nothing after it.

Before stopping, read back your own last line. If it does not begin `RECIPE `,
or it sits inside a code fence, or anything comes before or after it on that
line, the turn is not finished — fix it. The driver reads the last line and
nothing else, so a question asked in prose leaves the run with no way forward.
