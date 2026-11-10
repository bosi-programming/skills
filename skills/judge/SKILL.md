---
name: judge
description: Check a ticket, or a parent and its sub-issues, for readiness before any design: a lint, then a judge sub-agent for open decisions, "same as X" shorthand, unstated shapes and manual checks with no reason. Comments ## Ready, or ## Not ready with a blocking issue, and stops. Runs alone on a work card or under open-restaurant. Use when someone wants a ticket or a parent checked for gaps before work starts, or this gate redone on a card.
---

# judge

The readiness gate, run before anything is designed. It is a stage on a line, a parent's line included, which `open-restaurant` runs through `assembly-line`, and it also runs alone. A hard gate: gaps stop the
run; they are never answered on the issue's behalf. Prefix each log line
`restaurant:` under `open-restaurant`, `unattended:` in a headless run,
`judge:` when run alone.

## Input

The path to a card. A work card is the markdown file that carries a task from
one stage to the next; its shape is
`../feature-recipe/references/recipe-card-template.md`, and its `task` names one
ticket. A service card is the one `../open-restaurant/SKILL.md` opens; its
`parent` names a parent issue. Read the issue, its comments and every sub-issue
through the session's tracker tool.

Parent mode when the card is a service card or the issue has sub-issues:
all four rules. One-ticket mode otherwise: only `open-decision` and
`manual-reason`.

With no card, neither `task` nor `parent`, or an issue the tracker cannot read,
stop, write nothing else, and end `not-ready` with `runStatus: blocked`.

## Output

The same card, with this stage's parts written:

- `## Decisions` — the verdict line.
- `## Open Questions` — on `not-ready`, one `g<n>` entry per gap.
- `runStatus` — `blocked` on `not-ready`; untouched on `ready`.
- `runQuestion` — `g1` on `not-ready`, only when the card has the field.
- `lastTouched`.

The tracker gets the comment and issue of sections 3 and 4. The verdict is
`ready` or `not-ready`. The stage leaves `phase` and `phasesCompleted` as they
are.

## Settings

Resolve the key and the section from the settings file as
`../setup/references/config.md` describes, without opening that file:
`grep -n -A8 '^open-restaurant:' .bosi-skills.md ~/.bosi-skills.md`, current
folder first, then `$HOME`, then the default:

- `open-restaurant.judgeModel` — the model of the judge sub-agent. Default
  `''`: the session's model.

The readiness standard and the readiness lint come from the settings file's
`## open-restaurant` section, read under `## judge` once that section exists.

## 1. Lint

Run the readiness lint the section names, with the input it asks for. With none
named, skip to the judge and have it check the lint's ground too: in parent
mode every sub-issue has acceptance criteria, one repo, and a blocks graph with
no cycle; in one-ticket mode the ticket has acceptance criteria and one repo. A
lint that fails to run does not pass the gate: log it and treat it as a gap.

## 2. Judge

One sub-agent on `open-restaurant.judgeModel`, with no tools, reads the issue
(and its sub-issues) against the readiness standard the section names and
checks only what a lint cannot: `open-decision` (a choice the text leaves
open), `parity-shorthand` (a "same as X" with no criteria of its own),
`missing-contract` (a shape passed between sub-issues that neither states),
`manual-reason` (a manual check with no reason). On one ticket it checks only
`open-decision` and `manual-reason`. It returns
`{ ready, gaps: [{ issue, items: [{ rule, message }] }] }`.

## 3. Not ready

On any gap, create a "Readiness gaps: <id> — <title>" issue that blocks the
parent (in one-ticket mode, the issue) and lists each gap, comment `## Not ready <id>` on the issue with every
gap, write each gap to `## Open Questions` as `g1`, `g2`, …, set
`runStatus: blocked` (and `runQuestion: g1` where the card has the field), log
the verdict to `## Decisions`, and end `not-ready`. A tracker write that fails
is logged; the verdict stays `not-ready`.

## 4. Ready

Comment `## Ready <id>` on the issue, log verdict `ready` to `## Decisions`,
update `lastTouched`, and end `ready`. The line goes on.

## Headless

Read `../feature-recipe/references/headless.md`. In a headless run:

- Prefix each log line `unattended:`. Nothing in it waits on a person.
- Gaps are never answered on the issue's behalf.
- A gap is not a one-way door but a stop.

### Ending a run

On `not-ready`:

1. Make section 3's writes.
2. Set `runStatus: blocked` and `runQuestion` to the first gap's id. Leave
   `runNext`, `phase` and `phasesCompleted` alone.
3. Log the stop to `## Decisions`.
