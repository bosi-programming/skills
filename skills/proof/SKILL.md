---
name: proof
description: Post the proof for a parent and its sub-issues after QA — a Proof comment on each PR with the criteria it owns, each with its verdict and evidence, and one Proof comment on the parent with every parent criterion, its evidence uploaded to the tracker, and each PR with how many of its criteria are met. Runs alone on a work card, under open-restaurant, or as a stage on a line. Use when someone wants a parent's or a ticket's proof posted, or this step redone on a card.
---

# proof

The proof step for a parent and its sub-issues, or one ticket, run after `qa`.
`open-restaurant` runs its section 9 through this skill, and it also runs alone.
Prefix each log line `restaurant:` under `open-restaurant`, `unattended:` in a
headless run, `proof:` when run alone.

## Input

The path to a card. A work card is the markdown file that carries a task from
one stage to the next; its shape is
`../feature-recipe/references/recipe-card-template.md`, and its `task` names the
parent, or the one ticket. The sub-issues and each one's PR come from the
session's tracker tool, and one ticket's PR is the card's `prUrl`. A service
card is the one `../open-restaurant/SKILL.md` opens; its `parent` names the
parent and `## Sub-issues` gives each row's `PR` and `card`. Either card may
hold the `## QA` section `../qa/SKILL.md` writes. `<parent>` is the identifier
as the card writes it; with one ticket it is the ticket.

With no card, neither `task` nor `parent`, or no PR at all (no PR in
`## Sub-issues`, no `prUrl`, none on the tracker), stop, write nothing else, set
`runStatus: blocked` and log it. There is no verdict.

## Output

The same card, with this stage's parts written:

- `## Proof` — the link of each comment posted, PR and parent; made when
  missing.
- `## Decisions` — the verdict line.
- `## Open Questions` — `p1` when a post does not land.
- `runStatus` — `blocked` on bad input or `p1`, untouched otherwise.
- `runQuestion` — `p1`, only where the card has the field.
- `lastTouched`.

The stage also posts `## Proof` on each PR and one `## Proof <parent>` comment
on the parent. The verdict is `done` or `blocked`. The stage leaves `phase`,
`phasesCompleted` and `stage` as they are.

## Settings

No key. Guidance comes from the settings file's `## open-restaurant` section,
found as `../setup/references/config.md` describes (current folder first, then
`$HOME`). Read it under `## proof` once that section exists.

## 1. Criteria

For each sub-issue (or the one ticket), list the criteria it owns, from the
tracker, and the parent's criteria. Each criterion's verdict and evidence come
from `proof/<issue>/<n>/verdict.json` under `./qa-proof/<parent>/` when QA
proved it; else from that sub-issue's card (the row's `card`, or this card with
one ticket), its `## Quality Gate Results`; else `not proved`. A manual
criterion stays pending with its owner and does not count as met. No `## QA` is
not bad input.

## 2. Proof on each PR

Write `## Proof` on each sub-issue's PR: the criteria it owns, each with its
verdict and evidence. Write the body to a file and post with
`gh pr comment <pr> --body-file <file>`. A re-run posts a new comment: the
latest `## Proof` comment wins.

## 3. Proof on the parent

Write one `## Proof <parent>` comment on the parent through the session's
tracker tool: one entry per parent criterion with its evidence uploaded to the
tracker and linked, then a `### Sub-issues` list with each PR and how many of
its criteria are met. A row with no PR is listed as `no PR`.

## 4. Check the posts

Read back each post (`gh pr view <pr> --json comments`, and the parent's
comments through the tracker tool). A post that did not land is retried once.
Still missing: write `p1` to `## Open Questions`
(`- p1 — proof: <post> did not land on <target> — options: retry | post by hand — recommendation: retry — answer:`),
set `runStatus: blocked` and `runQuestion` to `p1` where the card has the field,
log verdict `blocked`, update `lastTouched`, and end `blocked`.

## 5. Done

Write each comment's link to the card's `## Proof`, log verdict `done` to
`## Decisions`, update `lastTouched`, and end `done`.

## Headless

Read `../feature-recipe/references/headless.md`. In a headless run:

- Prefix each log line `unattended:`. Nothing in it waits on a person.
- A post that does not land is a stop with `runStatus: blocked`, never answered
  on a person's behalf.
- It never merges, never edits a PR's code, and never moves a tracker state.

### Ending a run

On `p1`, make section 4's writes, leave `runNext`, `phase` and `phasesCompleted`
alone, and log the stop to `## Decisions`.
