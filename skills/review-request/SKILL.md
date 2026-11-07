---
name: review-request
description: Ask for review once a parent's or a ticket's PRs are ready — wait on each PR's checks, then post one message naming every PR to the review channel the settings name, tagging the mapped review groups, and attach the message link. Red checks, a timeout or no channel skip the request and say why. Runs alone on a work card, under open-restaurant, or as a stage on a line. Use when someone wants review requested for open PRs, or this step redone on a card.
---

# review-request

The review request step for a parent and its sub-issues, or one ticket, run once
the PRs are ready for review. `open-restaurant` runs its section 10's approve
step through this skill, and it also runs alone. Prefix each log line
`restaurant:` under `open-restaurant`, `unattended:` in a headless run,
`review-request:` when run alone.

## Input

The path to a card. A work card is the markdown file that carries a task from
one stage to the next; its shape is
`../feature-recipe/references/recipe-card-template.md`, and its `task` names the
parent, or the one ticket. The sub-issues and each one's PR come from the
session's tracker tool, and one ticket's PR is the card's `prUrl`. A service
card is the one `../open-restaurant/SKILL.md` opens; its `parent` names the
parent and `## Sub-issues` gives each row's `PR`. `<parent>` is the identifier
as the card writes it; with one ticket it is the ticket.

With no card, neither `task` nor `parent`, or no open PR at all (no PR in
`## Sub-issues`, no `prUrl`, none on the tracker), stop, write nothing else, set
`runStatus: blocked` and log it. There is no verdict.

## Output

The same card, with this stage's parts written:

- `## Review Request` — the verdict, each PR with its check state, the message
  link, any unmapped team and the skip reason; made when missing.
- `## Decisions` — the verdict line.
- `runStatus` — `blocked` on bad input, untouched otherwise.
- `lastTouched`.

The stage also posts one chat message and attaches its link on the tracker. The
verdict is `requested` or `skipped` with the reason. The stage leaves `phase`,
`phasesCompleted`, `gate` and `stage` as they are.

## Settings

Resolve the key as `../setup/references/config.md` describes, without opening
it: `grep -n -A12 '^open-restaurant:' .bosi-skills.md ~/.bosi-skills.md`, the
current folder first, then `$HOME`, then the default:

- `open-restaurant.reviewChannel` — the chat channel the request goes to.
  Default `''`: no request.

Guidance comes from the settings file's `## open-restaurant` section: its
review ready and review groups entries. Read it under `## review-request` once
that section exists.

## 1. Open PRs

List the open PRs: each row's `PR` in `## Sub-issues`, the card's `prUrl` with
one ticket, else the sub-issues' PRs on the tracker. A closed or merged PR is
left out. A row with no PR is named `no PR` in `## Review Request`.

## 2. Checks

Wait for each PR's checks the way the section's review ready entry says;
without one, `gh pr checks <pr> --watch`, with a timeout only when the entry
names one. A PR with no checks reported counts as green. All green goes on to
section 3. Any red, or a timeout, skips the request: verdict `skipped`, with a
reason naming each such PR and its state; go to section 4 with no link.

## 3. Request

When `open-restaurant.reviewChannel` is empty, verdict `skipped`, reason
`no channel`. Otherwise post one message there through the session's chat tool,
naming every PR, tagging the review groups the section's review groups entry
maps from the team. Never guess a group: an unmapped team gets no tag and a line
in `## Review Request`. Read the message back; one that did not land is retried
once. No chat tool, or a post still missing: verdict `skipped` with the reason.
A chat failure does not stop the run.

## 4. Link

Write `## Review Request` to the card: the verdict, each PR and its check state,
the message link, unmapped teams, the skip reason. On `requested`, attach the
message link through the session's tracker tool to the parent, or to the one
ticket.

## 5. Done

Log the verdict to `## Decisions`, update `lastTouched`, and end `requested` or
`skipped`.

## Headless

Read `../feature-recipe/references/headless.md`. In a headless run:

- Prefix each log line `unattended:`. Nothing in it waits on a person.
- It never merges, never edits a PR's code, never marks a PR ready or draft,
  and never moves a tracker state.

### Ending a run

On bad input, make section `## Input`'s writes, leave `runNext`, `phase` and
`phasesCompleted` alone, and log the stop to `## Decisions`. A `skipped` verdict
is not a stop.
