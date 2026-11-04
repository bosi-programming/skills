---
name: test
description: Write the failing tests for a ticket from the work card — every case in the TDD Test Mapping, written to the Interfaces before any code, run and seen to fail. The build stage after plan-code. Runs alone on a work card, or with no card finds or makes one. Use when someone wants the tests for a planned ticket written first, or this stage redone on a card.
---

# test

Write the tests that prove the plan, before any code exists, and see each one
fail. The tests come from the card, not from the code, so the code cannot bend
them.

`feature-recipe` and `recipe-relay` run this stage through this skill, and it
also runs alone.

## Input

The path to a work card, the markdown file that carries a task from one stage
to the next. Its shape is `../feature-recipe/references/recipe-card-template.md`.
The stage reads the card's `## Acceptance Criteria`, `## Testing Strategy`,
`## TDD Test Mapping` and `## Interfaces`.

With no card, load, read completely and execute
`../feature-recipe/phases/phase-0-start.md`. It finds the card for the task or
makes one, then routes back here. A card with neither `plan-code` nor the old
`mise-en-place` in `phasesCompleted` has no test cases yet: Phase 0 routes it
to the stage it still needs. A card with no `## Interfaces` gets that section
first: run section 4 of `../plan-code/SKILL.md`, then come back.

## Output

The same work card, with this stage's parts written:

- Failing tests on the branch, committed.
- `## TDD Test Mapping` — each case marked written, with its test's name.
- `## Decisions` — one line for the stage.
- `## Open Questions` — any gap nothing could settle.
- Frontmatter — `phase` set to `test`, `test` appended to `phasesCompleted`
  once, even on a redo, `lastTouched` updated.

## 1. Find the standards

Before writing anything, find what governs tests here: the repo's own
documented standards (a `CODING_STANDARDS.md`, `CONTRIBUTING.md`, or whatever
it documents), if any. These win wherever they conflict with what follows.
Load the bundled `code-standards` skill too, from `../code-standards/SKILL.md`,
or by name if that path is not where it lives, and read its testing files.

## 2. Write the tests

Write every case in `## TDD Test Mapping` before any code, from the
Acceptance Criteria, the Testing Strategy and `## Interfaces`. Test the names
and signatures `## Interfaces` gives, and nothing else. This stage never opens
a code file the plan names: it reads the card and the test files, so the tests
hold the plan and not the code someone wrote to it.

For a bug fix, write the regression case first.

Run the tests and confirm they fail. An import error for a name that does not
exist yet counts as a fail. A test that passes before any code means the
behaviour may already exist: stop and investigate rather than moving on, and
settle it with the user before you keep it.

Mark each case written in `## TDD Test Mapping`, with its test's name. Stage
and commit only the test files you wrote, by path, and retry a commit that hits
`index.lock`.

## 3. Close the stage

Say which tests got written, against the mapping, and how each one failed.
Append one line to `## Decisions`. Update the frontmatter — `phase: 'test'`,
append `test` to `phasesCompleted` (once, even on a redo), `lastTouched`.

## 4. Stage done

> **Stage done. [C] Continue here (recommended) — write the code to these tests now. [N] New session.**

**C:** load, read completely, and execute
`../code/SKILL.md`.

**N:** confirm the card is saved, tell the user to resume with the same
trigger phrase in a new session. End the session.

## Headless

`../feature-recipe/references/headless.md` holds the rules for a headless run.
Read it. In a headless run:

- Set `runNext: test` as you start.
- A test that passes before any code gets logged to `## Decisions` as
  `unattended:`, with its name; leave it in and carry on.
- Section 3 is unchanged — the frontmatter is updated either way.
- Section 4 does not apply. This stage does not stop at its own boundary: it
  loads, reads completely and executes
  `../code/SKILL.md`, and the run continues through
  `code`, `prepare-pr` and Documentation. A run stops at the
  recipe's end or at a one-way door, never at a stage boundary.

### Ending a run

Only if this stage is where the run stops — a plan too vague to name what a
test should check, or a test that cannot run at all for a reason outside the
card:

1. Set `runStatus: needs-input` for a one-way door or `blocked` for something
   external that has to change, and `runQuestion` to the id of the entry you
   wrote in `## Open Questions`. Leave `runNext` as `test`: that is what a
   resume re-runs.
2. Log the stop to `## Decisions`.
