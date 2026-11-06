---
name: reproduce
description: Try to reproduce a bug ticket on origin/<default branch> in one sub-agent that changes no tracked file; reproduced writes what it tried to ## Reproduction and the line goes on; not reproduced comments ## Blocked on the ticket with what it tried and stops the line blocked. Runs alone on a work card or under open-restaurant. Use when someone wants a bug checked before work starts, or this step redone on a card.
---

# reproduce

The bug reproduction step, run before a bug's design. `open-restaurant` runs
item 4 of its section 4 through this skill, and it also runs alone. Prefix each
log line `restaurant:` under `open-restaurant`, `unattended:` in a headless run,
`reproduce:` when run alone.

## Input

The path to a work card. A work card is the markdown file that carries a task
from one stage to the next; its shape is
`../feature-recipe/references/recipe-card-template.md`, and its `task` names the
bug ticket. Under `open-restaurant` it is the sub-issue's own card, which
`../open-restaurant/SKILL.md` opens, run in its repo's checkout. Read the ticket
and its comments through the session's tracker tool.

The stage does not judge whether the ticket is a bug: the line, or
`open-restaurant`'s bug marker, decides.

With no card, no `task`, a ticket the tracker cannot read, or a folder that is
not a git checkout, stop, write nothing else, set `runStatus: blocked` and log
it. There is no verdict.

## Output

The same card, with this stage's parts written:

- `## Reproduction` — what it tried and what it saw; on `not-reproduced`, the
  first line is `Comment: <link>`; made when missing.
- `## Decisions` — the verdict line.
- `## Open Questions` — on `not-reproduced`, entry `r1`.
- `runStatus` — `blocked` on `not-reproduced` and bad input; untouched on
  `reproduced`.
- `runQuestion` — `r1` on `not-reproduced`, only where the card has the field.
- `lastTouched`.

On `not-reproduced` the stage also posts the `## Blocked <id>` comment on the
ticket. The verdict is `reproduced` or `not-reproduced`. The stage leaves
`phase` and `phasesCompleted` as they are.

## 1. Try

One sub-agent tries to reproduce the bug on `origin/<default branch>`, after
`git fetch`, following the ticket's steps. It may run commands and tests. It
edits no tracked file, commits nothing and pushes nothing, so uncommitted work
in the checkout stays. It returns what it tried, each command or step, and what
it saw.

## 2. Not reproduced

If the bug did not happen, comment `## Blocked <id>` on the ticket, `<id>` the
ticket identifier, with what it tried and what it saw. Write `## Reproduction`:
first line `Comment: <link>` with the comment's link, then what it tried. Write
`r1` to `## Open Questions`
(`- r1 — reproduce: <id> did not reproduce on origin/<default branch> — options: add steps to the ticket | close the ticket — recommendation: add steps to the ticket — answer:`),
set `runStatus: blocked` and `runQuestion` to `r1` where the card has the field,
log verdict `not-reproduced` to `## Decisions`, update `lastTouched`, and end
`not-reproduced`. A tracker write that fails is logged and the stage stops with
`runStatus: blocked`.

## 3. Reproduced

If the bug happened, write what it tried and saw to `## Reproduction`, log
verdict `reproduced` to `## Decisions`, update `lastTouched`, and end
`reproduced`. Post no comment. The line goes on.

## Headless

Read `../feature-recipe/references/headless.md`. In a headless run:

- Prefix each log line `unattended:`. Nothing in it waits on a person.
- A bug that does not reproduce is never fixed or guessed at on the ticket's
  behalf.
- `not-reproduced` is a stop with `runStatus: blocked`, not a one-way door.

### Ending a run

On `not-reproduced`:

1. Make section 2's writes.
2. Set `runStatus: blocked` and `runQuestion` to `r1`, where the card has the
   field. Leave `runNext`, `phase` and `phasesCompleted` alone.
3. Log the stop to `## Decisions`.
