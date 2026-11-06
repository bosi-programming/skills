---
name: integrate
description: List the criteria a parent's QA proves, then in each repo checkout build a local integration/<parent> branch from origin/<default branch> by merging every sub-issue branch in blocks order, never pushing it; an empty scope ends no-scope, a merge conflict stops the line needs-input naming the two branches. Runs alone on a work card or under open-restaurant. Use when someone wants a parent's branches merged into one local branch for QA, or this step redone on a card.
---

# integrate

The integration step for a parent and its sub-issues, run before QA.
`open-restaurant` runs item 1 of its section 8 through this skill, and it also
runs alone. It never pushes `integration/<parent>`. Prefix each log line
`restaurant:` under `open-restaurant`, `unattended:` in a headless run,
`integrate:` when run alone.

## Input

The path to a card. A work card is the markdown file that carries a task from
one stage to the next; its shape is
`../feature-recipe/references/recipe-card-template.md`, and its `task` names the
parent. The sub-issues, the branch name the tracker gives each, and the blocks
relations come from the session's tracker tool, and every branch goes into the
current folder's checkout. A service card is the one
`../open-restaurant/SKILL.md` opens; its `parent` names the parent, and
`## Sub-issues` gives each row's `repo`, `branch`, `blocked by` and `card`; each
repo's checkout is `./<repo>/`. A service card means parent mode, a work card
means one-repo mode. `<parent>` is the parent identifier as the card writes it.

With no card, neither `task` nor `parent`, a parent with no sub-issues, an issue
the tracker cannot read, a missing checkout or a folder that is not a git
checkout, uncommitted changes to tracked files in a checkout, or a cycle in
blocks order, stop, write nothing else, set `runStatus: blocked` and log it.
There is no verdict.

## Output

The same card, with this stage's parts written:

- `## Integration` — `### QA scope`: the criteria in scope, each with its
  issue; `### Branches`: per repo, the `integration/<parent>` head sha, each
  merged ref with its sha in merge order, and each skipped row with why; made
  when missing.
- `## Decisions` — the verdict line.
- `## Open Questions` — on `conflict`, entry `i1`.
- `runStatus` — `needs-input` on `conflict`, `blocked` on bad input or a guarded
  rebuild, untouched on `integrated` and `no-scope`.
- `runQuestion` — `i1` on `conflict`, only where the card has the field.
- `lastTouched`.

The stage also leaves a local `integration/<parent>` branch in each repo
checkout, never pushed. The verdict is `integrated`, `no-scope` or `conflict`.
The stage leaves `phase` and `phasesCompleted` as they are.

## Settings

No key. Guidance comes from the settings file's `## open-restaurant` section,
found as `../setup/references/config.md` describes (current folder first, then
`$HOME`): its QA scope entry names the sub-issue criteria the parent QA proves.
Read it under `## integrate` once that section exists.

## 1. Scope

List the criteria the parent QA proves: every criterion of the parent, plus each
sub-issue criterion the section's QA scope names; with none named, each
sub-issue criterion its card says needs the running, integrated system (on a
work card, the sub-issue's own text). Write the list to `## Integration` under
`### QA scope`. If the list is empty, build no branch, write `none` under
`### QA scope`, log verdict `no-scope` to `## Decisions`, update `lastTouched`,
and end `no-scope`.

## 2. Integrate

Run `git fetch`. In each repo checkout, create `integration/<parent>` from
`origin/<default branch>` with
`git switch -C integration/<parent> origin/<default branch>`, and merge the
sub-issue branches into it in blocks order with
`git merge --no-ff --no-edit <ref>`. `<ref>` is `origin/<branch>` when it
exists, else the local `<branch>`. A row with neither is skipped and listed
under `### Branches`. It never pushes `integration/<parent>`.

An `integration/<parent>` that already exists is rebuilt, as it is on a return
from `qa`. If it holds a commit that no merged ref and no
`origin/<default branch>` holds, stop, drop nothing, set `runStatus: blocked`
and log it.

## 3. Conflict

On a merge conflict, run `git merge --abort`, so the checkout is clean on
`integration/<parent>` with the merges before it. Name the two branches: the one
it was merging, and the merged ref or `origin/<default branch>` that last
touched a conflicting file: run `git log -1 --format=%ct <ref> -- <file>` on
each of them and take the one with the newest time.
Write `i1` to `## Open Questions`
(`- i1 — integrate: <branch a> and <branch b> conflict in <repo> on <files> — options: fix the conflict on <branch b> | change the blocks order — recommendation: fix the conflict on <branch b> — answer:`),
set `runStatus: needs-input` and `runQuestion` to `i1` where the card has the
field, write the merges so far to `### Branches`, log verdict `conflict` to
`## Decisions`, update `lastTouched`, and end `conflict`.

## 4. Integrated

After the last merge in every repo, write `### Branches` to `## Integration`,
leave each checkout on `integration/<parent>` for QA, log verdict `integrated`
to `## Decisions`, update `lastTouched`, and end `integrated`.

## Headless

Read `../feature-recipe/references/headless.md`. In a headless run:

- Prefix each log line `unattended:`. Nothing in it waits on a person.
- A conflict is never resolved on the branches' behalf.
- `conflict` is a stop with `runStatus: needs-input`.
- It never pushes, force-pushes or drops a commit.

### Ending a run

On `conflict`:

1. Make section 3's writes.
2. Set `runStatus: needs-input` and `runQuestion` to `i1`, where the card has
   the field. Leave `runNext`, `phase` and `phasesCompleted` alone.
3. Log the stop to `## Decisions`.
