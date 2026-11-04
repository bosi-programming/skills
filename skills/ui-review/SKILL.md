---
name: ui-review
description: Compare the screenshots of a changed screen with the design attached to the ticket a work card names, rate each difference critical, major or minor, write a ## UI Review section and end pass, fail or inconclusive. The stage after code when a change reaches a screen. Runs alone on a work card. Use when a change to a screen needs checking against its design, or this review redone on a card.
---

# ui-review

The stage after `code` when the change reaches a surface a person sees.
`recipe-relay` runs its UI review through this skill, and it also runs alone.
When a driver hands project rules, paste them word for word under a
`Project rules:` line at the end of the reviewer's prompt. Prefix each log line
`relay:` under `recipe-relay`, `unattended:` in a headless run, `ui-review:`
when run alone.

## Input

The path to a work card: the markdown file that carries a task from one stage
to the next, shaped as
`../feature-recipe/references/recipe-card-template.md`. Its `task` names the
ticket that carries the design. Its `## Solution` names the changed surface.
The screenshots are in `{scratch}/ui-review/`, captured by `code`'s fix and
taste step.

With no card, stop and write nothing. With that folder empty or missing, or a
summary that says `none: <reason>`, the verdict is `inconclusive` with the
reason, and no reviewer starts.

## Output

The same card, with this stage's parts written:

- `## UI Review` — the verdict and every finding with its design region and
  screenshot.
- `## Quality Gate Results` — minor findings.
- `## Decisions` — the verdict line, and the reason when `inconclusive`.
- `## Open Questions` — only when a headless run stops.
- `lastTouched`.

The verdict is `pass`, `fail` or `inconclusive`. The stage leaves `phase` and
`phasesCompleted` as they are, and never edits code or takes screenshots.

## Settings

Resolve the key from the settings file as `../setup/references/config.md`
describes, without opening that file:
`grep -n -A8 '^recipe-relay:' .bosi-skills.md ~/.bosi-skills.md`, current
folder first, then `$HOME`, then the default:

- `recipe-relay.uiReviewerModel` — the model of the reviewer sub-agent. Default
  `''`, which keeps the model the session runs on.

## 1. Design

The design is the image attached to the task, read with whatever tool the
session has for the tracker. A design-tool frame the task links may settle a
region the image leaves unclear, but never stands in for a missing image. No
design at all makes the verdict `inconclusive`. The reviewer never guesses the
design from the task's text.

## 2. Compare

Spawn one sub-agent on `recipe-relay.uiReviewerModel`. It never starts the app
and takes no screenshots: it judges the ones in `{scratch}/ui-review/`.

Walk the design top to bottom and name, for each difference, the design region
and the screenshot it comes from. Rate it: critical when the changed surface is
missing, blank or broken; major for a wrong component or structure, a missing or
extra field, wrong content or order, or a state the design shows that the build
lacks; minor for small spacing, colour or weight drift and anything the image
cannot settle. Judge what a person sees, not the code. Write the verdict and the
findings to a `## UI Review` section on the card.

## 3. Verdict

Any critical or major finding: `fail`. None, or only minor: `pass`. No
screenshots or no design: `inconclusive`.

Minor findings never send work back: log them to `## Quality Gate Results`. On
`fail` the line goes back to the latest `code`, with the screenshots' paths and
the critical and major findings, then runs this stage again; at most twice, then
`needs-input`. This stage does not run `code` itself. A second run on the same
card appends a `Round <n>` block to `## UI Review` instead of replacing it.

Log the verdict to `## Decisions`, update `lastTouched`, and end with the
verdict.

## Headless

Read `../feature-recipe/references/headless.md`. In a headless run:

- Nothing in it waits on a person.
- Prefix each log line `unattended:`.
- It never edits code, merges, force-pushes or deletes work written on purpose.

### Ending a run

This applies to a person's headless run of this skill, not under
`recipe-relay`, whose section 4 stops a third `fail`. On a question with no
reasonable default:

1. Write an entry to `## Open Questions`.
2. Set `runStatus: needs-input` and `runQuestion` to its id.
3. Leave `runNext`, `phase` and `phasesCompleted` alone.
4. Log the stop to `## Decisions`.
