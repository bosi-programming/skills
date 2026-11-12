---
name: security-review
description: Review the diff a work card's change makes for security flaws against OWASP Top 10 2021 and ASVS 4.0.3 level 1, in one reviewer sub-agent, write a ## Security Review section and end pass or fail. The stage after code when the change touches auth, secrets or input from outside. Runs alone on a work card. Use when a change needs a security pass, or this review redone on a card.
---

# security-review

The stage after `code` when the change touches security: auth, sessions,
permissions, secrets, crypto, parsing of outside input, or a dependency added
or bumped. `code` raises the `touches-security` signal and the line adds this
stage after it. `assembly-line` and `recipe-relay` run it through this skill,
and it also runs alone. When a driver hands project rules, paste them word for
word under a `Project rules:` line at the end of the reviewer's prompt. Prefix
each log line `relay:` under `recipe-relay`, `line:` under `assembly-line`,
`unattended:` in a headless run, `security-review:` when run alone.

## Input

The path to a work card: the markdown file that carries a task from one stage
to the next, shaped as
`../feature-recipe/references/recipe-card-template.md`. Its `task` names the
ticket. Its `## Solution` says what the change is meant to do. The diff runs
from a fixed point to `HEAD`. The fixed point is the one the driver's project
rules name; with none, the merge-base of `HEAD` with `origin/<default branch>`.

With no card, stop and write nothing.

## Output

The same card, with this stage's parts written:

- `## Security Review` — the verdict and every finding, one line each:
  `- <severity> — <file>:<line> — <check id> — <what is wrong>`.
- `## Quality Gate Results` — medium and low findings.
- `## Decisions` — the verdict line, and `empty diff` when there is nothing to
  review.
- `## Open Questions` — only when a headless run stops.
- `lastTouched`.

The verdict is `pass` or `fail`. The stage leaves `phase` and `phasesCompleted`
as they are, and never edits code.

## 1. Diff

List the diff from the fixed point to `HEAD`. The fixed point is the one the
driver's project rules name; with none, the merge-base of `HEAD` with
`origin/<default branch>`. An empty diff is `pass`: log
`empty diff` to `## Decisions` and start no reviewer. The reviewer reads only
what the diff changes and the code around it that it needs to judge a line.

## 2. Review

Spawn one reviewer sub-agent with the diff, `## Solution` and
[`./references/checks.md`](./references/checks.md). It never edits code. It
checks what a diff can show against the Top 10 and ASVS level 1 rows, and names
for each finding the file, the line, the check id (an OWASP Top 10 2021
category such as `A02:2021`, or an ASVS 4.0.3 requirement id such as
`V2.10.4`) and a severity: `critical`, `high`, `medium` or `low`, starting from
the default in the checks file and moved by what the code does. A finding that
is not a flaw in the diff, such as a secret in a test fixture or a placeholder,
is still reported, rated by what it is. Write the verdict and the findings to a
`## Security Review` section on the card.

## 3. Verdict

Any `critical` or `high` finding: `fail`. None, or only `medium` and `low`:
`pass`. An empty diff: `pass`.

Medium and low findings never send work back: log them to
`## Quality Gate Results`. On `fail` the line goes back to the latest `code`,
with the critical and high findings, then runs this stage again; at most twice,
then `needs-input`. This stage does not run `code` itself. A second run on the
same card appends a `Round <n>` block, headed `### Round <n>`, to `## Security Review` instead of
replacing it.

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
