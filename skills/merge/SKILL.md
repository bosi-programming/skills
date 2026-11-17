---
name: merge
description: The last human gate on a line. Check the PRs a work card or a parent's service card names for open review threads, stop for a person unless auto gates are on, and on approval merge them in blocks order, retarget stacked PRs and move the tickets to their done state. Runs alone on a work card or under open-restaurant. Use when someone wants a ticket's PRs or a parent's PRs merged behind a human gate, or this gate redone on a card.
---

# merge

The last human gate on every line. It is a stage on a line, a parent's line included, which `open-restaurant` runs through `assembly-line`, and it also runs alone. This skill never merges without a
person approving at the gate, unless auto gates are on: see _Auto gates_. Prefix each log line `restaurant:` under
`open-restaurant`, `unattended:` in a headless run, `merge:` when run alone.

## Input

The path to a card. A work card is the markdown file that carries a task from
one stage to the next; its shape is
`../feature-recipe/references/recipe-card-template.md`. Its `task` names the
ticket, and its PRs are `prUrl` and every PR under `## PR`, in that order. A
service card is the one `../open-restaurant/SKILL.md` opens; its `parent` names
a parent issue, and its PRs are the PR column of `## Sub-issues`, ordered by
`blocked by`, with `base` naming a stacked PR's base.

Parent mode when the card is a service card. One-ticket mode on a work card. A
PR already merged counts as merged, so a resume skips it.

With no card, no PR, or a PR closed without merging, stop, write nothing else,
set `runStatus: blocked`, and log it. The stage never ran, so there is no
verdict.

## Output

The same card, with this stage's parts written:

- `## Merge` — the merged, failed and pending lists, and any open threads; made
  on a work card when missing.
- `## Decisions` — the verdict line.
- `runStatus` — `gate` at the gate, `terminal` on `merged`, `needs-input` on
  `threads-open`, `blocked` on bad input.
- `gate` — `merge`, only where the card has the field.
- `lastTouched`.

The tracker gets the moves and comment of section 4. The verdict is `merged` or
`threads-open`. The stage leaves `phase`, `phasesCompleted` and `status` as they
are.

## Settings

Resolve the key and the section from the settings file as
`../setup/references/config.md` describes, without opening that file:
`grep -n -A8 '^open-restaurant:' .bosi-skills.md ~/.bosi-skills.md`, current
folder first, then `$HOME`, then the default:

- `open-restaurant.doneState` — the state a merged ticket, and a parent with no
  open criterion, moves to. Default `Done`; `''` means no move.

Guidance comes from the settings file's `## open-restaurant` section, read under
`## merge` once that section exists.

## 1. Threads

For each PR not yet merged, read its unresolved review threads through `gh`
(GraphQL `reviewThreads`, `isResolved`). On any unresolved thread, list them per
PR in `## Merge`, log the verdict `threads-open` to `## Decisions`, set
`runStatus: needs-input`, update `lastTouched`, and end `threads-open`; the stage
merges nothing. The line returns to `review-fix`, at most twice, then a human
gate.

## 2. Gate

Stop for a human unless auto gates are on: set `runStatus: gate` and `gate: merge` where the
card has the field, write the pending list to `## Merge`, and report the PRs.
Approval is a person's answer in chat in the session that resumes it; without
it the stage stays at the gate. On approval, go on to section 3.

## 3. Merge

Merge in blocks order. A ticket's PRs come one after another; a stacked PR gets
its retarget to the default branch once its blocker merges, and merges after it.
A failed merge stops at the gate again, with the merged, failed and pending
lists in `## Merge`. On approval, resume from the failed one. Merge with
`gh pr merge`; never `--admin`, never force-push.

## 4. Done

After the last merge, move every merged ticket (the work card's `task`, or each
merged sub-issue) to `open-restaurant.doneState` unless it is empty. In parent
mode, move the parent there only if proof leaves no criterion open; else comment
`## Open criteria <parent>` listing each one. Set `runStatus: terminal`, log
verdict `merged` to `## Decisions`, update `lastTouched`, and end `merged`.

## Auto gates

The stage is on only when its prompt holds the line `Auto gates: on`. With no
such line it is off, and sections 2 and 3 run as written.

When on, section 2 takes the recommendation instead of stopping. It approves
when every PR not yet merged passes all three tests:

- `gh pr checks` on each PR shows every check passing, none pending or failing;
- `gh pr view <pr> --json reviewDecision` is not `CHANGES_REQUESTED`;
- section 1 found no unresolved thread.

Log `<prefix> auto-gate: merge gate took approve` to `## Decisions` (an `auto-gate:` line), then go on
to section 3. When any PR fails a test, take no recommendation: stop at the
gate as section 2 says, with the failing PRs and the test each failed in
`## Merge`. Pending or failing checks and a requested change fall back to the
human gate; no new verdict exists.

A failed `gh pr merge` stops at the gate again, with the merged, failed and
pending lists in `## Merge`, and logs `<prefix> auto-gate: merge failed`. The
stage never retries it by itself. It never uses `--admin` and never
force-pushes. Threads still open past the return limit end `needs-input`, as
section 1 says: the recommendation there is `stop`, logged as
`<prefix> auto-gate: merge past limit took stop`.

## Headless

Read `../feature-recipe/references/headless.md`. In a headless run:

- Prefix each log line `unattended:`.
- A headless run never approves on a person's behalf, so it always ends at the
  gate, except under _Auto gates_ above.
- It never force-pushes or deletes work.

### Ending a run

At the gate:

1. Set `runStatus: gate`, and `gate: merge` where the card has the field.
2. Leave `runNext`, `phase` and `phasesCompleted` alone.
3. Log the stop to `## Decisions`.
