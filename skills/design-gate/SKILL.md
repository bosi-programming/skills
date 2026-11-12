---
name: design-gate
description: Post the plan plan-code wrote for a ticket that changes a database schema, a migration or a public contract as one new ticket comment, then stop at a human gate for a person to approve it or ask for changes. Added after plan-code by its schema-change signal. Runs alone on a work card. Use when a risky plan needs a person to read it before any code, or this gate redone on a card.
---

# design-gate

The gate between a risky plan and its code. When `plan-code` writes a plan that
changes a database schema, a migration or a public contract, it raises
`schema-change` in `## Signals`, and `assembly-line` adds this stage right
after `plan-code`. The stage posts the plan on the ticket and stops for a
person to approve it or ask for changes. It never sits on a saved line.

It runs as a stage under `assembly-line`, and also runs alone. When a driver
hands project rules, paste them word for word under a `Project rules:` line at
the end of the prompt. Prefix each log line `relay:` under `recipe-relay`,
`line:` under `assembly-line`, `unattended:` in a headless run, and
`design-gate:` when run alone.

## Input

The path to a work card, the markdown file that carries a task from one stage
to the next, shaped `../feature-recipe/references/recipe-card-template.md`.
Its `task` names the ticket; its `## Solution`, `## Implementation Plan` and
`## Interfaces` hold the plan `plan-code` wrote.

## Output

The same card, with this stage's parts written:

- `## Decisions` — the `Plan comment:` line, then one line for the verdict.
- `## Open Questions` — the gate question while the stage waits.
- `runStatus` — `gate` while the stage waits for a person.
- `lastTouched`.

The verdict is `approved` or `changes`. The stage leaves `phase` and
`phasesCompleted` alone, opens no ticket and commits no code.

## 1. Read the plan

Read the card's `## Solution`, `## Implementation Plan` and `## Interfaces`,
and the `schema-change` lines in `## Signals`, which name the plan lines that
brought the stage onto the line.

With no card, no `task`, a ticket the tracker cannot read, or a card missing
`## Solution`, `## Implementation Plan` or `## Interfaces`, stop: nothing posted.
Write an entry to `## Open Questions` naming what is missing, set
`runStatus: blocked` and log it. There is no verdict.

## 2. Post the plan

Post the plan as one new comment on the ticket the card's `task` names, through
the session's tracker tool. It opens with a `## Plan for review` heading and the
attribution line, then the `schema-change` evidence lines, then the card's
`## Solution`, `## Implementation Plan` and `## Interfaces` as they stand.

A rerun after `changes` posts a new comment: never edit an old one, so the
thread keeps each round of the plan.

Write `Plan comment: <link>` to `## Decisions`. With no tracker tool in the
session, post nothing: the plan stays on the card, the line reads
`Plan comment: not posted — no tracker tool`, and the gate question says the
plan was not posted.

## 3. Gate

The comment of section 2 is posted before the gate, so a person can read it
while the line waits. Set `runStatus: gate`. Write the question to
`## Open Questions` ("approve the plan of <ticket>, or say what to change"),
post it in chat and stop. The stage is `gate: human`: `assembly-line` resumes
it with the person's answer.

- Approval: log `<prefix> design-gate approved` to `## Decisions`, update
  `lastTouched` and end `approved`. The line continues with the step after this
  one.
- A request for changes: log `<prefix> design-gate changes — <what to change>`
  to `## Decisions`, in the person's words, so the next `plan-code` reads them.
  Update `lastTouched` and end `changes`. The line goes back to the latest
  `plan-code` at most twice, then to a person. The rerun of `plan-code` raises
  `schema-change` again, and this stage posts a new comment.

## Headless

Read `../feature-recipe/references/headless.md`. In a headless run:

- Prefix each log line `unattended:`.
- A bad input stops with `runStatus: blocked`; a question with no reasonable
  default sets `runStatus: needs-input`.
- Section 3 is the stop: the run waits for a person, since approving a plan
  that changes a schema, a migration or a public contract is not a decision
  the run takes for them.

### Ending a run

At the gate, and on a bad input:

1. Write the entry to `## Open Questions`.
2. Set `runStatus: gate` at the gate, `blocked` on a bad input, or
   `needs-input` on a question with no default, and `runQuestion` to the
   entry's id where the card has the field. Leave `runNext`, `phase` and
   `phasesCompleted` alone.
3. Log the stop to `## Decisions`.
