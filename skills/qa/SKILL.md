---
name: qa
description: Bring up one env for a parent, prove each criterion in QA scope on the local integration/<parent> branch with saved evidence, and on a fail send the fix to the owning branch fast-forward only, rebuild through integrate and run again, at most twice, before a human gate. Runs alone on a work card, under open-restaurant, or as a stage on a line. Use when someone wants a parent's integrated branches QA'd and fixed, or this step redone on a card.
---

# qa

The QA and fix step for a parent and its sub-issues, or one ticket, run after
`integrate`. It is a stage on a line, a parent's line included, which `open-restaurant` runs through `assembly-line`, and it also runs alone. Prefix each log line `restaurant:` under
`open-restaurant`, `unattended:` in a headless run, `qa:` when run alone.

## Input

The path to a card. A work card is the markdown file that carries a task from
one stage to the next; its shape is
`../feature-recipe/references/recipe-card-template.md`, and its `task` names the
parent, or the one ticket. The sub-issues come from the session's tracker tool,
and every checkout is the current folder's. A service card is the one
`../open-restaurant/SKILL.md` opens; its `parent` names the parent,
`## Sub-issues` gives each row's `repo` and `branch`, and `## Contract` holds
the contract; each repo's checkout is `./<repo>/`. Either card must hold the
`## Integration` section `../integrate/SKILL.md` writes, with `### QA scope`
(the criteria to prove) and `### Branches` (each repo's merged refs).
`<parent>` is the identifier as the card writes it.

With no card, neither `task` nor `parent`, no `## Integration` or no
`### QA scope` in it, a missing checkout, or a checkout not on
`integration/<parent>`, stop, write nothing else, set `runStatus: blocked` and
log it. There is no verdict. A `### QA scope` reading `none`: end `pass`, run
nothing and log it.

## Output

The same card, with this stage's parts written:

- `## QA` — one `### Round <n>` per QA round: each criterion with its verdict
  and evidence path, the QA checks' result, the fixes with sha and owner; made
  when missing.
- `## Decisions` — the verdict line.
- `## Open Questions` — `qa1` at a human gate.
- `runStatus` — `gate` at a human gate, `blocked` on bad input, untouched
  otherwise.
- `runQuestion` — `qa1` at a human gate.
- `gate` — `qa` at a human gate.
- `qaRounds` and `fixChecks` — the counts.
- `lastTouched`.

`gate`, `qaRounds`, `fixChecks` and `runQuestion` are written only where the
card has the field. The stage also leaves evidence under `./qa-proof/<parent>/`,
one `proof/<issue>/<n>/verdict.json` per criterion, and a `## QA <parent>`
comment per round on the parent. The verdict is `pass`, `fail`, `inconclusive`
or `blocked`. The stage leaves `phase`, `phasesCompleted` and `stage` as they
are.

## Settings

Resolve each key as `../setup/references/config.md` describes, without opening
it: `grep -n -A8 '^open-restaurant:' .bosi-skills.md ~/.bosi-skills.md`, the
current folder first, then `$HOME`, then the default.

- `open-restaurant.envName` — name of the QA env; `{parent}` is the parent
  identifier in lower case. Default `{parent}`.
- `open-restaurant.qaModel` — model of the QA agent. Default `''`, the session's
  model.
- `open-restaurant.fixModel` — model of the agent that fixes failed criteria.
  Default `''`.

Guidance comes from the settings file's `## open-restaurant` section: its QA
skill, QA env, QA checks and fix check entries. Read it under `## qa` once that
section exists.

## Under a line

If the card's `## Decisions` holds an entry prefixed `line:`, a line runs this
stage. Run section 1; on `pass` run section 2; on `fail` make section 3's
writes; then end with the verdict. Do not run sections 4 to 6: the line follows
`return` in `./stage.json`. `fail` goes back to `code` on the ticket's branch,
then `integrate`, at most twice; `inconclusive` and `blocked` go to a person.

## 1. QA

Bring up one env named from `open-restaurant.envName`, the way the section's QA
env entry says: one env for the parent, never per sub-issue. With no QA env
entry, there is no env to bring up or tear down: QA runs in the checkouts. One
sub-agent on `open-restaurant.qaModel` follows the QA skill the section names,
or, with none, proves each criterion in `### QA scope` by running the integrated
system. It saves evidence under `./qa-proof/<parent>/`, one
`proof/<issue>/<n>/verdict.json` per criterion, and a manual criterion stays
pending with its owner. It never edits the checkouts. It returns `pass`, `fail`,
`inconclusive` or `blocked`. Run the section's QA checks on its output, add one
to `qaRounds`, and post the round as `## QA <parent>` on the parent and as
`### Round <n>` under `## QA` in the card. Then: `pass` to section 2, `fail` to
section 3, `inconclusive` or `blocked` to section 6.

## 2. On pass

Tear the env down, log verdict `pass` to `## Decisions`, update `lastTouched`,
and end `pass`.

## 3. On fail

Save the proof bundle, tear the env down, switch every checkout off
`integration/<parent>` (to `origin/<default branch>`, detached), then go to
section 4, or end `fail` under a line.

## 4. Fix

This is the `code` return in `stage.json`, run here when no line runs the stage.
One sub-agent on `open-restaurant.fixModel`. For each failed criterion it picks
one owning sub-issue: the criterion's own, else the contract's producer (the
parent's latest `## Contract` comment), else the branch that touched the failing
files; on a work card with no sub-issues, the ticket's own branch. It fixes on a
detached HEAD of `origin/<owner branch>`, commits
`fix(<owner>): <criterion id> <summary>`, and pushes fast-forward only: never
`--force`, and never on `integration/<parent>`. It returns
`{ fixes: [{ criterion, owner, branch, repo, sha, summary }] }`.

## 5. Fix check

Run the section's fix check, or, with none: each sha sits on
`origin/<owner branch>` and each checkout is clean. Add one to `fixChecks`. A
refused fix goes back to the fix agent. Once all land, load, read completely and
execute `../integrate/SKILL.md` on the same card, which rebuilds
`integration/<parent>` from the new tips. On `integrated`, go back to section 1
and re-run every criterion in scope. On `conflict` it has set
`runStatus: needs-input` and `i1`: stop, no verdict.

## 6. Limits

QA to fix runs at most 2 times, and fix to fix check at most 4 times; past
either, stop at a human gate. `inconclusive` and `blocked` also go to the human
gate. At a human gate, write `qa1` to `## Open Questions`
(`- qa1 — qa: <verdict> on <criteria> after <n> rounds — options: approve another round | stop — recommendation: <one> — answer:`),
set `runStatus: gate` and `gate: qa` where the card has the field, set
`runQuestion` to `qa1`, log the verdict, update `lastTouched`, and end with the
last verdict. A `blocked` the human approves goes to section 4, with the blocker
counted in scope.

## Headless

Read `../feature-recipe/references/headless.md`. In a headless run:

- Prefix each log line `unattended:`. Nothing in it waits on a person.
- A human gate is a stop with `runStatus: gate`, never answered on a person's
  behalf.
- It never force-pushes, never pushes `integration/<parent>`, never merges.

### Ending a run

At a human gate, make section 6's writes, leave `runNext`, `phase` and
`phasesCompleted` alone, and log the stop to `## Decisions`.
