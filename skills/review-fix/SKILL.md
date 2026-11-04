---
name: review-fix
description: Run better-code-review headless on the open PR a work card names, then fix its findings by their Verified tag, test first, push to the PR and log what got rejected. The stage after prepare-pr. Runs alone on a work card. Use when someone wants a PR reviewed and its findings fixed, or this stage redone on a card.
---

# review-fix

The stage after `prepare-pr`, run on a card whose PR is open. `recipe-relay`
runs its section 5 through this skill, and it also runs alone. When a driver
hands project rules, paste them word for word under a `Project rules:` line at
the end of each sub-agent prompt.

## Input

The path to a work card, the markdown file that carries a task from one stage
to the next. Its shape is `../feature-recipe/references/recipe-card-template.md`.
The stage reads the card's `task` as the spec and its `prUrl` as the open PR.

With no card, no `prUrl`, or a PR that is not open, stop before the review,
write nothing, and end `blocked`.

## Output

The same work card, with this stage's parts written:

- `## Quality Gate Results` — each `judgement call` and `scope creep` finding.
- `## Decisions` — each rejected finding, the review's `Reviewed:` line and
  each `Not verified:` entry.
- `## Open Questions` — only when a headless run stops.
- `lastTouched`.

Fixes go to the open PR, which stays ready for review. The stage leaves `phase`
and `phasesCompleted` as they are.

## Settings

Resolve two keys from the settings file as
`../setup/references/config.md` describes, without opening that file:
`grep -n -A8 '^recipe-relay:' .bosi-skills.md ~/.bosi-skills.md`, current
folder first, then `$HOME`, then the default:

- `recipe-relay.routineModel` — the model of the review sub-agent. Default
  `''`: the session's model.
- `recipe-relay.codingModel` — the model of the fix sub-agent. Default `''`:
  the session's model.

## 1. Review

Spawn one `general-purpose` sub-agent on `recipe-relay.routineModel` to run
`../better-code-review/SKILL.md` with `--headless`. The fixed point is the
merge base of the work branch and the default branch; if the work ran on the
default branch itself, it is the commit before the work's first one. The spec
source is the task on the card. Have it write the review's output as it stands
to `{scratch}/review.txt` and return only its `Totals:` line.

## 2. Fix

Spawn one sub-agent on `recipe-relay.codingModel` to work through the findings
in that file, on the same branch, by their `Verified:` tag. A `ran` finding is
proved: go to the fix. A `read` finding gets read at its `file:line` first. A
`no` finding: verify it first, by running or reading what it names, and reject
it if it does not hold. Log each `judgement call` and `scope creep` finding to
`## Quality Gate Results` and leave the code as it is; deleting work written on
purpose is a one-way door. Write a failing test first where the finding is a
behaviour, then fix, then run the project's scoped tests and lint. Push to the
open PR, which stays ready for review. Log each finding you reject to
`## Decisions`, with the reason, instead of changing the code: prefix the line
`relay:` under `recipe-relay`, `unattended:` in a headless run, `review-fix:`
when run alone. Log the review's `Reviewed:` line and each `Not verified:`
entry there too, so the gap stays on the card. Return at most 150 words: what
got fixed, what got rejected and why, what stays not verified.

## 3. Report

Tell the user, in short bullets, which findings were fixed and which were
rejected, with the reason, and what the review left not verified. Update
`lastTouched`. End `done`.

## Headless

Read `../feature-recipe/references/headless.md`. In a headless run:

- Nothing in it waits on a person.
- Section 3's report goes to `## Decisions` as `unattended:` lines instead of
  chat.
- It never merges, force-pushes or deletes work written on purpose.

### Ending a run

A finding whose fix is a one-way door, or a question with no reasonable
default:

1. Write an entry to `## Open Questions`.
2. Set `runStatus: needs-input` and `runQuestion` to its id. Leave `runNext`,
   `phase` and `phasesCompleted` alone.
3. Log the stop to `## Decisions`.
