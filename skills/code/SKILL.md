---
name: code
description: Write the code for a ticket from the work card to the tests test wrote, make them pass, then hold it at a hard gate — better-code-review plus the project's own scoped tests, lint and type-check — until every check passes or is honestly deferred to CI. The build stage after test. Runs alone on a work card, or with no card finds or makes one. Use when someone wants the code for a planned, tested ticket written and checked, or this stage redone on a card.
---

# code

Turn the tests on the branch into passing code, then verify it before anything
leaves for review. The second half is a hard gate: `prepare-pr` opens no PR
until everything here passes.

`feature-recipe` and `recipe-relay` run this stage through this skill, and it
also runs alone. Once it starts, it runs to its end without stopping for user
input except the one check-in in section 4 — recommend the user switch to
auto-accept-edits mode if they haven't already, then continue regardless of
their answer.

## Input

The path to a work card, the markdown file that carries a task from one stage
to the next. Its shape is `../feature-recipe/references/recipe-card-template.md`.
The stage reads the card's `## Solution`, `## Implementation Plan`,
`## Interfaces`, `## TDD Test Mapping` and the Testing and Config sections.

With no card, load, read completely and execute
`../feature-recipe/phases/phase-0-start.md`. It finds the card for the task or
makes one, then routes back here. A card with no `test` in `phasesCompleted`
has no tests yet: Phase 0 routes it to `../test/SKILL.md` first.

## Output

The same work card, with this stage's parts written:

- Code on the branch, committed, with the mapped tests passing.
- `## TDD Test Mapping` — any case added for a gap the code turned up.
- `## Quality Gate Results` — the review's `Reviewed:` line and
  `Not verified:` entries, judgement calls, what passed, and what is deferred
  to CI and why.
- `## Signals` — `no-screen-change` when the change touches no surface a
  person sees.
- `## Decisions` — one line for the stage, and any deviation from the plan.
- `## Open Questions` — any gap nothing could settle.
- Frontmatter — `phase` set to `code`, `code` appended to `phasesCompleted`
  once, even on a redo, `lastTouched` updated.

## Beside test

When a driver runs this stage beside `test`, at the same time and on the same
branch, it is the code writer. It runs sections 1 and 2 only, minus the step
that runs the tests: it never opens a test file, and it does not add tests. It
writes the code, commits only the files it wrote, by path, and returns. The
driver runs this skill again once both writers are done, from step 3 of
section 2, to make the tests pass and run the rest of the stage.

## 1. Find the standards

Before writing anything, find what governs style and structure here: the
repo's own documented standards (a `CODING_STANDARDS.md`, `CONTRIBUTING.md`,
or whatever it documents), if any — these win wherever they conflict with
what follows. Always load the bundled `code-standards` skill too, whether or
not the repo has its own — from `../code-standards/SKILL.md`, or by name if
that path isn't where it lives — and read the files that govern the kind of
code this task touches; skip the ones it can't violate.

## 2. Write the code

The tests are already on the branch: `test` (`../test/SKILL.md`) wrote every
case in `## TDD Test Mapping` and saw each one fail.

Work through the Implementation Plan one step at a time. For each step:

1. Say what's about to change.
2. Make the implementation change, holding it against the standards found
   above as you write, not as an afterpass once it's done.
3. Run the tests this step maps to (from `## TDD Test Mapping`) and confirm
   they now pass. Fix the code, not the test, unless the test contradicts
   `## Interfaces` or the Acceptance Criteria. If a gap turns up — behavior
   the existing tests don't cover — write a test for it, confirm it fails,
   then close the gap, and add the case to `## TDD Test Mapping`.
4. Commit.
5. If anything deviated from the plan or needed a judgement call, append it
   to a running decisions log — don't stop, keep implementing. If the plan
   itself needs to change, update the relevant work card section rather
   than quietly drifting from what it says.

Apply config changes from the Testing/Config sections of the card as they
come up in the plan, and note what was changed.

## 3. Confirm it actually behaves

Once implementation is done, run the app or the affected surface and confirm
the change behaves the way the Acceptance Criteria describe — this is
checking the real thing works, not just that the tests are green.

## 4. Check in once, with everything

If the decisions log from section 2 has entries, present it to the user in
one message, get their input, and apply anything they flag. If the log is
empty, don't wait for a reply — note "no deviations" and fall straight
through to the review.

## 5. Run the review

Invoke the `better-code-review` skill (Skill tool) against the change, then
triage its findings by axis without waiting for the user:

- **Standards** — better-code-review already separates hard violations
  (documented-standard breaches) from judgement calls (baseline-smell
  heuristics). Fix the hard violations; log judgement calls to
  `## Quality Gate Results` rather than acting on them.
- **Spec** — fix "missing requirement" and "implemented but wrong" findings
  autonomously. Never auto-remove code for a "scope creep" finding —
  deleting work that was deliberately written is a one-way door; log those
  to `## Quality Gate Results` for the user instead.
- **Tests** — fix the hard violations and write each missing test, failing
  first where the behaviour allows it. Log judgement calls to
  `## Quality Gate Results` rather than acting on them.

The review already ran the project's scoped tests, lint and type-check at the
commit on its `Reviewed:` line, and tags each finding `ran`, `read` or `no`.
Keep that result: copy the `Reviewed:` line and every `Not verified:` entry to
`## Quality Gate Results`.

## 6. Detect this project's own checks

Where `HEAD` is still the commit on the review's `Reviewed:` line, sections 6
to 9 run only the checks the review lists as not verified; the rest already
ran on this exact code. Once a fix from section 5 moves `HEAD`, run them all.

Don't assume a specific test runner, linter, or scoping convention — read
what this repo actually has: `package.json` scripts, CI workflow files, any
project-specific "test changed files" or "lint changed files" target. Use
whatever the project already provides for scoping to what changed, rather
than running its full suite from a standing start.

## 7. Determine what changed

List the changed files against the base branch. Filter to source and test
files — everything written so far; the PR-chunking decision hasn't been made
yet at this point (`prepare-pr` decides it in the next stage).

## 8. Run tests scoped to the change

Use the project's own scoped-test mechanism if it has one. If it doesn't,
and there's no reasonable way to scope locally (no per-file test runner, a
type system that needs full-project context, etc.), don't fall back to
running the whole suite from here — say plainly that full verification for
this piece will happen once a PR opens and CI runs it, and note that in
`## Quality Gate Results` rather than pretending it ran locally.

## 9. Run lint and type-check scoped to the change

Same rule: scoped to the changed files where the project supports that,
deferred to CI and noted as such where it doesn't. Never fall back to a
full-project lint or type-check run — that's what freezes machines.

## 10. Fix and retry

For every failure: diagnose it, propose a fix, get it applied, re-run just
that check. Once everything's been touched, re-run the whole set from
section 8 again. Loop until every check that could run locally passes, or
is honestly marked deferred to CI.

## 11. Close the stage

Summarize what was implemented against the Implementation Plan. Write the
results — what passed, what's deferred to CI and why — to
`## Quality Gate Results`. When the change touches no surface a person sees,
write `no-screen-change` to `## Signals`. Append one line to `## Decisions`.
Update the frontmatter — `phase: 'code'`, append `code` to `phasesCompleted` (once, even
on a redo), `lastTouched`.

## 12. Stage done

This menu only appears once every local check passes or is honestly marked
deferred — not before.

> **Stage done. [N] New session (recommended) — resume the next stage fresh. [C] Continue here.**

**N:** confirm the card is saved, tell the user to resume with the same
trigger phrase in a new session. End the session.

**C:** load, read completely, and execute `../prepare-pr/SKILL.md`.

## Headless

`../feature-recipe/references/headless.md` holds the rules for a headless run.
Read it. In a headless run:

- Set `runNext: code` as you start, so a run that dies here can be picked up
  from the card.
- Section 4's check-in is taken, not asked: take the recommendation, log it to
  `## Decisions` prefixed `unattended:`, and keep going.
- Section 5 runs `better-code-review` with `--headless`, so the review asks
  nothing and returns its findings as text.
- Section 5's scope-creep findings are logged with `unattended:` and the code
  they describe stays where it is. Deleting work on a recommendation is a
  one-way door, and a run stops for those rather than opening them.
- Sections 6 to 11 are unchanged: detect the project's own checks, scope them
  to the change, fix what fails, write `## Quality Gate Results` — including
  what was deferred to CI and why — and update the frontmatter.
- Section 12 does not apply. This stage does not stop at its own boundary: it
  loads, reads completely and executes `../prepare-pr/SKILL.md`, and the run
  continues through `prepare-pr` and Documentation. A run stops at the
  recipe's end or at a one-way door, never at a stage boundary.

### Ending a run

Only if this stage is where the run stops:

1. Set `runStatus: needs-input` for a one-way door or `blocked` for something
   external that has to change, and `runQuestion` to the id of the entry you
   wrote in `## Open Questions`. Leave `runNext` as `code`: that is what a
   resume re-runs.
2. Log the stop to `## Decisions`.
