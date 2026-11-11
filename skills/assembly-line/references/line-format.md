# Line format

A line is the list of stages one ticket runs, in order. `plan-assembly-line`
writes it in a comment on the ticket; `assembly-line` reads that comment and
runs each stage; `validate-line.py` checks it before anything runs. Each stage
declares what it takes, delivers and where it goes back to in its `stage.json`;
see [`./stage-spec.md`](./stage-spec.md). The line says only which stages run
and in what order.

## Where it lives

In a comment on the ticket, or in a local line file: the JSON object alone,
at the path `assembly-line.lineFile` names (`{cardsDir}/{ticket}.line.json`).
When both exist, `assembly-line` takes the file. The work card stays the
hand-off between stages:
the line names the stages, the card carries what they read and write.

The same JSON object can stand alone as a file, so a saved line in the repo
uses this format too, with `name` in place of `ticket`.

## Marker

A line comment opens with a `## Assembly line` heading and a sentence or two
for people, then holds one ```json block. The block is the line; readers ignore
the prose around it.

A comment is a line comment when its ```json block parses to an object with
`"format": "assembly-line/1"`. The heading helps a person find it; the `format`
field is what a reader looks for, because the tracker may change headings and
drop HTML comments when it renders markdown.

~~~markdown
## Assembly line

Small fix with no screen change, so no `test` or `ui-review`.

```json
{
  "format": "assembly-line/1",
  "ticket": "BOS-1",
  "stages": ["judge", "evaluate-ticket", "plan-code", "code", "prepare-pr", "review-fix", "merge"]
}
```
~~~

| Key | Type | What it holds |
| --- | --- | --- |
| `format` | string | Always `assembly-line/1`. A new version gets a new value. |
| `ticket` | string | The ticket the line is for. A reader stops if it does not match the ticket the comment is on. |
| `name` | string | In a saved line, its name, equal to the file name; in place of `ticket`. |
| `stages` | list | The stages, in order. See below. A line comment may use `from` instead. |
| `from` | string | A line comment only: the saved line to start from, in place of `stages`. See `## Saved lines`. |
| `drop` | list | With `from`: stage names to remove. |
| `add` | list | With `from`: `{"after": <stage>, "item": <item>}` entries to insert. |

## Stages and inputs

`stages` lists the stages in the order they run. Each item is one of:

- A stage name: a skill under `skills/` with a `stage.json`, such as `"code"`.
- A stage object, `{"stage": "<name>", "with": {...}}`, when the stage needs
  something for this ticket that is not on the card, such as a URL to review.
  `with` holds plain keys and values; the stage's `SKILL.md` says which it reads.
- A parallel group, `{"parallel": [...]}`. See below.
- A sub-issue group, `{"group": "sub-issues"}`. See below.

The line never repeats what a stage reads from the card: that is `takes` in
the stage's `stage.json`. Nor does it say where a person must step in: that is
`gate` in the same `stage.json`. A stage with `gate: human` stops the run for
a person on every line it appears on.

A stage may appear more than once, as `code` does after a parallel group with
`test`. A `return` in `stage.json` goes back to the latest stage with that name.

## Parallel groups

`{"parallel": [<item>, <item>, ...]}` runs its branches at the same time. Each
branch is a stage name or a stage object. The group ends when every branch
ends, and the next item starts only then. A failing verdict in any branch
follows that branch's `return`.

## More than one line comment

The line comment created last wins; the others are ignored. To change a line,
post a new line comment rather than editing the old one, so the ticket keeps
the history. `assembly-line` writes the link of the comment it ran to
`## Decisions` on the card.

## Sub-issue groups

A parent's line holds `{"group": "sub-issues"}` where its sub-issues run.
Each sub-issue runs its own line, from its own line comment, in the order its
blocks relations set. A sub-issue's line runs without its `merge`: the parent's
`merge` merges them all, as `merge` does in parent mode from `## Sub-issues`.
A sub-issue with no line comment stops the group with `runStatus: needs-input`
and names `plan-assembly-line`.

## Saved lines

Common lines live in the repo, one file each, in [`./lines/`](./lines/):
`feature`, `bug`, `small-fix` and `parent`. A saved line has `"format"`,
`"name"` (equal to the file name) and `stages`, and no `ticket`.

A line comment may start from one: it holds `"from": "<saved line>"` in place
of `stages`, with optional `"drop"` (a list of stage names) and `"add"` (a list
of `{"after": "<stage>", "item": <item>}`). Expansion goes in this order:

1. Copy the saved line's stages.
2. Remove every dropped stage, at the top level and from parallel branches. A
   parallel group left with no branch goes. `judge` and `merge` cannot be
   dropped.
3. Apply each add in list order, right after the last top-level stage named in
   `"after"`.

A name to drop must be on the saved line, and `"after"` must be a top-level
stage on the line as it stands. A saved line has no `from` of its own.

`validate-line.py` expands the line, runs every rule on the expansion, and
prints it under `"line"`. A line comment keeps the `from` form; readers run
the expanded line. A rejected edit gives `saved-line` or `line-edit`.

## Rules

- The first stage is `judge`.
- `merge` is on the line, at the top level.
- After `merge`, only stages with `gate: auto` in their `stage.json`.
- Every stage name is a skill under `skills/`.
- `ticket` matches the ticket the comment is on.

`validate-line.py` enforces these and the rules that need the catalog:

- `line-parses`: the line file exists and holds JSON.
- `line-shape`: `format`, `ticket` or `name`, `stages` or `from`, `drop`, `add` and every item have the shapes above.
- `saved-line`: `from` names a saved line in `lines/` that parses and has the saved-line shape.
- `line-edit`: no `drop` of `judge`, `merge` or a stage not on the saved line; every `add` anchors on a top-level stage.
- `catalog-parses`: the catalog file exists and holds a `stages` object.
- `known-stage`: every stage name is in the catalog.
- `first-judge`: the first item is `judge`.
- `last-gate-merge`: `merge` is on the line at the top level.
- `auto-after-merge`: only `gate: auto` stages come after `merge`.
- `takes-met`: each `takes` is delivered by an earlier stage, by the stage itself, or at the start.
- `return-target`: every `return` target is a stage on the line.
- `parallel-group`: the branches of a group share no `delivers`.

`## Decisions`, `## Open Questions`, `## TDD Test Mapping` and the fields
`phase`, `phasesCompleted` and `lastTouched` may be shared by parallel
branches. A take is met from the start by `task`, `parent` and `## Sub-issues`.

## Example: full line

A feature with tests written beside the code, review fixes and docs:

```json
{
  "format": "assembly-line/1",
  "ticket": "BOS-1",
  "stages": [
    "judge",
    "evaluate-ticket",
    "plan-code",
    { "parallel": ["test", "code"] },
    "code",
    "prepare-pr",
    "review-fix",
    "code-docs",
    "merge"
  ]
}
```

`test` and `code` start together; `code` runs again once both end, to make the
new tests pass. `merge` is the only `gate: human` stage, so the run stops there
with a PR ready for review.

## Example: short line

A small fix with no new tests of its own:

```json
{
  "format": "assembly-line/1",
  "ticket": "BOS-2",
  "stages": ["judge", "evaluate-ticket", "plan-code", "code", "prepare-pr", "review-fix", "merge"]
}
```

## Example: parent line

A parent whose sub-issues each run their own line:

```json
{
  "format": "assembly-line/1",
  "ticket": "BOS-3",
  "stages": ["judge", "evaluate-ticket", { "group": "sub-issues" }, "merge"]
}
```

## Example: line from a saved line

A feature with no screen change:

```json
{
  "format": "assembly-line/1",
  "ticket": "BOS-4",
  "from": "feature",
  "drop": ["ui-review"]
}
```

## Check

Run from the repository root:

```bash
python3 skills/assembly-line/scripts/check-line-format.py
```

It fails, naming the part, when this file lacks an answer above, lacks the
full or short example, or holds an example that breaks a rule.
