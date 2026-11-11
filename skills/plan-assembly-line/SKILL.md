---
name: plan-assembly-line
description: Suggests each ticket's line of stages from its body and the stage catalog, starting from the saved line that matches the ticket's kind, validates it, lets the engineer confirm or edit it, and saves it as a line comment on the ticket only after approval. Use when plan-work hands off new tickets, when an engineer names tickets that need a line, or says "plan the line" or "plan assembly line".
---

# Plan Assembly Line

Suggests and saves each ticket's line: the ordered stages `assembly-line` runs for it. It never runs the line. It writes nothing to the tracker before the engineer approves.

## Input

One or more ticket ids. `plan-work` hands over the ids of the tickets it just saved, in its step 7 (`../plan-work/SKILL.md`). The engineer can also type them. Each ticket id may be a parent with sub-issues.

## 1. Read each ticket

Through the tracker tool in this session, read each ticket's body and comments. `../assembly-line/references/line-format.md` says what a line holds; read it here, and read `../assembly-line/references/catalog.json` for the stages.

A comment is a line comment when its json block parses to an object whose `"format"` is `assembly-line/1`. If the ticket has one, take the one created last. It is the starting suggestion. Saving posts a new line comment, which wins; the old one stays.

## 2. Suggest a line

Read the stages from `../assembly-line/references/catalog.json`. Offer only stages in that catalog. Every line starts at `judge` and ends at `merge`.

Start from the saved line that matches the ticket's kind. The saved lines are the files in `../assembly-line/references/lines/`: `feature`, `bug`, `small-fix` and `parent`. Pick by kind, in this order:

- A parent with sub-issues: `parent`. Its sub-issues join the list and get lines of their own. The saved line holds `{"group": "sub-issues"}`.
- No criterion tagged `[unit]`, `[int]`, `[e2e]` or `[story]`: `small-fix`.
- Title type `fix`: `bug`.
- Otherwise: `feature`.

Then apply these rules as `drop` and `add` edits on that saved line, each with `from`:

- Drop `ui-review` unless the ticket has a `## Design` section with a link, or a criterion tagged `[ui]` or `[story]`. A `- No visual change:` line does not count. On `small-fix`, add `ui-review` right after `code` when one of those holds.
- Drop `code-docs` unless the title type is `feat` or a criterion is tagged `[docs]`. On `small-fix`, add `code-docs` right after `review-fix` when a criterion is tagged `[docs]`.

If the ticket already has a line, start from it and change only what the rules require.

Each suggestion carries one or two sentences of why.

### Run log

The run log tells which stages earned their place for tickets of the same kind. Work out the kind, passed as `--kind`, from the block the ticket's body carries: `## Bug report` is Bug; `## Why this shape` or `## Removes` is Enablement; `## Design deliverable` is Design; `## Before → after` is Feature. A ticket with no kind block has no kind: skip the log for it.

Read the key `assembly-line.runLog` as `../setup/references/config.md` says: `grep -n -A8 '^assembly-line:' .bosi-skills.md ~/.bosi-skills.md`, the current folder first, then `$HOME`, then the default `~/.bosi-skills/runs.jsonl`. When the default holds, leave `--log` out. In the command below, `$SKILL_DIR` is this skill's folder.

```bash
python3 "$SKILL_DIR/scripts/stats.py" --kind <kind> --log <assembly-line.runLog>
```

`$SKILL_DIR/scripts/stats.py` prints one json object. Each stage in it has a `suggestion` and a `because`:

- `add`: a signal added the stage in more than half its runs. Show it only for a stage the line lacks.
- `look`: the stage failed in a quarter or more of its runs. Show it only for a stage the line holds.
- `cut`: the stage never failed. Show it only for a stage the line holds.

A stage with fewer 5 runs has a null suggestion. Show each `because` as it stands. A suggestion from the log is shown and not applied: the engineer decides. When the script exits 1 or 2, or the log has no runs, planning goes on without log, and the table says why.

## 3. Validate each line

Write each suggested line to `{scratch}/<ticket>.line.json` as the full line object from `../assembly-line/references/line-format.md`, with `format` (`assembly-line/1`), `ticket` and `stages`, not a bare list of stages. When the line starts from a saved line, the file holds `from`, with `drop` and `add`, in place of `stages`. In the command below, `$SKILL_DIR` is this skill's folder.

```bash
python3 "$SKILL_DIR/../assembly-line/scripts/validate-line.py" {scratch}/<ticket>.line.json
```

Run the validator, `$SKILL_DIR/../assembly-line/scripts/validate-line.py`, on every line before showing it. It prints a json object with `"valid"` and a list of errors, and for a `from` line the expanded stages under `"line"`; show those expanded stages, not the `from` form. Exit `0` means valid, `1` invalid, `2` a usage error.

Fix a suggestion of your own that fails, then run it again. For an error on a line the engineer edited, show its `stage` and `rule`. For a `takes-met` error, show the stage to add: the stage named after `delivered by` in the message. If the message says no stage in the catalog delivers it, say that.

## 4. Show and approve

Show one table of every ticket: the line, why, a From run log column and the validator result. The From run log column carries each `because` verbatim, or `-` when there is none. Suggestions from the log are not applied; an engineer edit takes one, and the edit is validated again. The engineer confirms or edits each line.

Nothing is written before the engineer approves. An edit is validated again. A line the validator rejects is not saved: show the errors and ask again. The engineer may approve some tickets and not others; only the approved ones go on to step 5.

## 5. Save

Post one comment per ticket, using the tracker tool the session has. Use the shape in `../assembly-line/references/line-format.md`: a `## Assembly line` heading, the why in a sentence or two, and one json block holding exactly the approved line: the `from` form as approved, not the expanded stages.

Never edit or delete an old line comment. A new comment replaces it, because the one created last wins.

If the session has no tracker tool, stop before writing and show the lines.

## 6. Read back

The skill reads it back: fetch each saved comment, parse its json block and check that it matches the approved line. A difference is reported, and the skill does not post again unless the engineer asks.

Reply with a link per ticket, and which tickets were not saved and why.
