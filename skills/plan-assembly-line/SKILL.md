---
name: plan-assembly-line
description: Suggests each ticket's line of stages from its body and the stage catalog, validates it, lets the engineer confirm or edit it, and saves it as a line comment on the ticket only after approval. Use when plan-work hands off new tickets, when an engineer names tickets that need a line, or says "plan the line" or "plan assembly line".
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

Start from the full line: `judge`, `evaluate-ticket`, `plan-code`, `{"parallel": ["test", "code"]}`, `code`, `prepare-pr`, `review-fix`, `code-docs`, `merge`. Then apply these rules:

- Drop the parallel group when no criterion is tagged `[unit]`, `[int]`, `[e2e]` or `[story]`.
- Add `ui-review` right after the last `code` when the ticket has a `## Design` section with a link, or a criterion tagged `[ui]` or `[story]`. A `- No visual change:` line does not count.
- Keep `code-docs` only when the title type is `feat` or a criterion is tagged `[docs]`.
- A parent with sub-issues gets `judge`, `evaluate-ticket`, `{"group": "sub-issues"}` and `merge`. Its sub-issues join the list and get lines of their own.

If the ticket already has a line, start from it and change only what the rules require.

Each suggestion carries one or two sentences of why.

## 3. Validate each line

Write each suggested line to `{scratch}/<ticket>.line.json` as the full line object from `../assembly-line/references/line-format.md`, with `format` (`assembly-line/1`), `ticket` and `stages`, not a bare list of stages. In the command below, `$SKILL_DIR` is this skill's folder.

```bash
python3 "$SKILL_DIR/../assembly-line/scripts/validate-line.py" {scratch}/<ticket>.line.json
```

Run the validator, `$SKILL_DIR/../assembly-line/scripts/validate-line.py`, on every line before showing it. It prints a json object with `"valid"` and a list of errors. Exit `0` means valid, `1` invalid, `2` a usage error.

Fix a suggestion of your own that fails, then run it again. For an error on a line the engineer edited, show its `stage` and `rule`. For a `takes-met` error, show the stage to add: the stage named after `delivered by` in the message. If the message says no stage in the catalog delivers it, say that.

## 4. Show and approve

Show one table of every ticket: the line, why, and the validator result. The engineer confirms or edits each line.

Nothing is written before the engineer approves. An edit is validated again. A line the validator rejects is not saved: show the errors and ask again. The engineer may approve some tickets and not others; only the approved ones go on to step 5.

## 5. Save

Post one comment per ticket, using the tracker tool the session has. Use the shape in `../assembly-line/references/line-format.md`: a `## Assembly line` heading, the why in a sentence or two, and one json block holding exactly the approved line.

Never edit or delete an old line comment. A new comment replaces it, because the one created last wins.

If the session has no tracker tool, stop before writing and show the lines.

## 6. Read back

The skill reads it back: fetch each saved comment, parse its json block and check that it matches the approved line. A difference is reported, and the skill does not post again unless the engineer asks.

Reply with a link per ticket, and which tickets were not saved and why.
