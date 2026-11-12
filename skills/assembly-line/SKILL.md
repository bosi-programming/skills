---
name: assembly-line
description: Runs the stages a ticket's line names, from its line comment or a local line file, in the line's order, each in its own sub-agent, taking every checkpoint's own recommendation; validates the line first, follows each stage's return on a failing verdict, and stops at the line's gates. Use when the user names one ticket and wants its line run, or says "run the line" or "assembly line".
---

# Assembly Line

Runs one ticket's line: the ordered stages its line comment names. It changes no stage's files, and `recipe-relay` stays as it is until BOS-112. This session orchestrates and stays live; each stage's work happens in a sub-agent told to take every checkpoint's own recommendation, so what reaches this chat is one line per stage, not a design question.

## Input

One ticket id. The line comes from the local line file, else from the ticket's line comment. Several tickets, or a parent with sub-issues, are the work of `open-restaurant`.

## Settings

Read the keys below as `../setup/references/config.md` says: look them up with `grep -n -A8 '^assembly-line:' .bosi-skills.md ~/.bosi-skills.md`, the current folder first, then `$HOME`, then the default.

- `assembly-line.codingModel` (`''`): model for the test writers, the code writers and the fix agent.
- `assembly-line.routineModel` (`''`): model for `prepare-pr`, `code-docs` and the review sub-agent.
- `assembly-line.uiReviewerModel` (`''`): model for the UI reviewer.
- `assembly-line.reviewState` (`In Review`): tracker state once the PR is open. Empty skips the move.
- `assembly-line.doneState` (`Done`): tracker state once `merge` merges. Empty skips the move.
- `assembly-line.runLog` (`~/.bosi-skills/runs.jsonl`): the file the run log goes to.
- `assembly-line.lineFile` (`{cardsDir}/{ticket}.line.json`): the local line file. `{cardsDir}` stands for `feature-recipe.cardsDir` and `{ticket}` for the ticket id; the path is relative to the project root.
- `assembly-line.lineDestination` (`ticket`): where `plan-assembly-line` saves a line, `ticket` or `file`. This skill reads both places whatever it holds.
- `feature-recipe.cardsDir` (`./recipes`): the folder the line board reads cards from; look it up with `grep -n -A8 '^feature-recipe:' .bosi-skills.md ~/.bosi-skills.md`.

An empty model keeps the model this session runs on.

Project rules come from the settings file's `## assembly-line` section, else its `## recipe-relay` section. Paste them word for word under a `Project rules:` line at the end of every sub-agent prompt this skill writes. A rule there beats a stage's default, never a stop condition in section 6. No section means no rules.

## 1. Read the line

Read the line before any card exists, from two places. First the line file: the path `assembly-line.lineFile` names, with `{cardsDir}` and `{ticket}` filled in. It holds the line's JSON object alone, the object a line comment's json block holds. Then, through the tracker tool in this session, read the ticket's comments and take the line comment created last: the one whose json block parses to an object whose `"format"` is `assembly-line/1`. When both exist, the file wins: someone saved it in this project on purpose. `./references/line-format.md` says what a line holds.

Stop and write nothing, naming `plan-assembly-line`, in each of these cases:

- there is no line comment and no line file;
- the line's `ticket` names another ticket;
- the line holds `{"group": "sub-issues"}`, which is `open-restaurant`'s work (a `from` line is checked after validation, below).

Write the line's JSON to `{scratch}/line.json`. In the command below, `$SKILL_DIR` is this skill's folder.

```bash
python3 "$SKILL_DIR/scripts/validate-line.py" {scratch}/line.json
```

The validator, `$SKILL_DIR/scripts/validate-line.py`, runs before any stage runs. When its `"valid"` is false, the run stops, writes nothing, and names each error's `stage` and `rule`; for a stage that lacks what it takes, it names the missing stage. Point the user to `plan-assembly-line`.

When the line has `from`, it starts from a saved line: the run uses the validator's `"line"`, the expanded line, from here on. Its stages are the ones run, and the `{"group": "sub-issues"}` stop is checked on the expanded line, so for a `from` line that check comes after validation.

Work out `kind` once, from the block the ticket's body carries: `## Bug report` is `Bug`; `## Why this shape` or `## Removes` is `Enablement`; `## Design deliverable` is `Design`; `## Before → after` is `Feature`. A ticket with none of them has `kind` `null`.

## 2. Find or make the card

Read and follow `../feature-recipe/phases/phase-0-start.md` in this session, only up to the point it has a card. Follow it as an interactive invocation: take the task from what the user already said, and don't write `runMode` to the card. Its routing is not followed: the line routes. Log the link to the line comment, or the path of the line file, to `## Decisions`, prefixed `line:`.

## 3. Run each stage

A step is one top-level item of the line: a stage name, a stage object (its `with` keys go into the prompt), or a parallel group. Run the steps one at a time. Note `startedAt` before each stage starts, as _Run log_ in section 5 says.

Each stage runs in its own sub-agent, a `general-purpose` one with full tool access, given the prompt in _Stage prompt_ below with the stage's `SKILL.md` as the file to load. `judge`, `ui-review`, `security-review` and `review-fix` run in this session instead, because their own steps spawn the sub-agents.

Models: `assembly-line.codingModel` for test writers, code writers and the fix agent; `assembly-line.routineModel` for `prepare-pr` and `code-docs`. Hand both to `review-fix`, in place of the `recipe-relay` model keys, and `assembly-line.uiReviewerModel` to `ui-review`.

`prepare-pr` opens the PR ready for review, never as a draft, and leaves it that way. This overrides its draft rule for deferred CI checks and its Headless rule that opens drafts. Tell it to skip its own review step, since `review-fix` reviews the diff, and to move the task, in the tracker the card came from, to `assembly-line.reviewState` once the PR is open.

A `{"parallel": ["test", "code"]}` group follows _Cooking in parallel_ below. Any other parallel group starts every branch at once and ends when all end.

### Stage prompt

> Load and execute the stage's `SKILL.md` against the recipe card at `{card path}`, with the stage's `with` keys, if the line gives any. Follow its own `## Headless` section for every checkpoint it names, taking the recommendation it states, and log it to `## Decisions` prefixed `line:` (a person is running this, just not being asked).
> Do not read `../feature-recipe/references/headless.md`: this prompt holds what you need from it. Stop and return control once the stage's closing section is written. Do not set `runMode` on the card. Never merge, delete work written on purpose, force-push, rewrite history, run an irreversible migration, or change credentials or production. At one of those, or at a question with no reasonable default, stop: write an entry to `## Open Questions` with an id, the question, the options and your recommendation; set `runStatus` to `needs-input` for a one-way door or `blocked` when something external must change; set `runQuestion` to the id; leave `runNext`, `phase` and `phasesCompleted` alone; and log the stop to `## Decisions`. Return at most 100 words on what got decided, and end the reply with `Verdict:` and the stage's verdict. The rest stays on the card.

### Cooking in parallel

Cooking splits so that tests and code get written at the same time, by agents that cannot shape one to the other. Run the steps below in order, every time a `test` and `code` group comes up, even when the task touches one repo. Run each test writer, code writer and fix agent on the model `assembly-line.codingModel` names. Its default, `''`, keeps the model this session runs on.

1. **Interfaces.** Section 4 of `plan-code` writes `## Interfaces` to the card before either writer starts: for each repo the plan touches, the public names, their signatures and the files they live in. Both writers code to that section and nothing else. A plan too vague to name them stops the run with `runStatus: needs-input`, as section 6 says. A card resumed at Cooking with no such section gets one sub-agent that runs that section of `plan-code`.
2. **Writers.** For each repo, spawn its test writer and its code writer at the same time, both on the same branch and worktree the code runs from: the repo's own checkout, on `{branch}`, the branch the repo is on. Start every pair before waiting on any of them. Each writer stages and commits only the files it wrote, by path, and retries a commit that hits `index.lock`.
   - The **test writer** loads `test` (`../test/SKILL.md`) with the stage prompt, limited to its repo. It reads the Acceptance Criteria, Testing Strategy, `## TDD Test Mapping` and `## Interfaces`, and never sees the code: it opens no file the code writer touches. It writes the tests for its repo, runs them, and confirms they fail; an import error for a name that does not exist yet counts as a fail. It commits and marks each case written in `## TDD Test Mapping`. A test that already passes gets logged to `## Decisions` as `line:`, with its name; the writer leaves it in and carry on. It stops after `test`'s section 3 and does not load `code`.
   - The **code writer** loads `code` (`../code/SKILL.md`) with the stage prompt, limited to its repo, and runs it as its _Beside test_ section says. It reads the Solution, Implementation Plan, Config changes and `## Interfaces`, and never sees the tests: it opens no test file. It writes the code for its repo and commits, without adding tests, holding to `code`'s standards and plan-drift rules, minus the step that runs the tests.
3. **Fix and taste.** Once both writers of every repo return, the `code` that follows the group is the fix and taste agent: one sub-agent loads `code` (`../code/SKILL.md`) again, as the stage prompt says, with the tests and code already in place on `{branch}`. It starts at step 3 of `code`'s section 2: run the tests, make the red ones pass by fixing the code, not the test, unless the test contradicts `## Interfaces` or the Acceptance Criteria. Then it runs the rest of `code`. Tell it to skip `code`'s section 5: the line's `review-fix` stage runs the one review, right after `prepare-pr`. With no review to lean on, `code` runs every project check itself, and those checks stay its hard gate.

### UI review

A UI review compares what the change renders with the design the task carries. Load, read completely and execute `../ui-review/SKILL.md` on the card in this session, handing it the project rules above and the model `assembly-line.uiReviewerModel` names.

Tell the latest `code` before it to screenshot into `{scratch}/ui-review/` once its checks pass: it clears the folder, brings the change up the way the project already does, and screenshots every state of the changed surface the Acceptance Criteria name. Once the screenshots are saved, it stops what it brought up. When it cannot bring the surface up, its summary says `none: <reason>`: the verdict is `inconclusive`, and no reviewer starts. An `inconclusive` verdict goes on the card with its reason, logged as `line:`, and the run moves on.

### Review and fix

When `prepare-pr` returns with a PR open, the branch holds the code. Run `review-fix` at once, whatever the card's `status` or `runStatus`; do not wait for `code-docs` or for `runStatus: terminal`. If the run stopped on `blocked` or `needs-input`, skip it.

Load, read completely and execute `../review-fix/SKILL.md` on the card in this session, handing it the project rules above, `assembly-line.codingModel` for its fix sub-agent and `assembly-line.routineModel` for its review sub-agent.

### Gates

A stage with `gate: human` in the catalog (today `merge`) runs its steps up to its gate in a sub-agent, which stops at `runStatus: gate`. The run then writes the question to `## Open Questions`, posts it in chat, and stops. Resumed with the person's approval, the gate stage runs in this session, with `assembly-line.doneState` in place of `open-restaurant.doneState`: it moves the ticket there once the merge lands. An empty value skips the move.

## 4. Go back on a failing verdict

A verdict with an entry in the stage's `return` in `./references/catalog.json` is failing. The run goes back to the latest step at or before this one that is, or holds, the entry's `to` stage, and runs forward again from there. Log each go-back as `line: return <stage> <verdict> -> <to> (<k>/<limit>)`.

Once the entry's `limit` is used up, its `past` decides: `needs-input` stops the run with `runStatus: needs-input`; `human` stops it with `runStatus: gate`, a question in `## Open Questions` and the same question in chat. A verdict with no `return` entry moves on, and is logged.

## 5. Move to the next stage

When a step returns, log `line: step <n>/<total> <stage> <verdict>` to `## Decisions`, keep `runNext` on the stage in flight so Phase 0 can resume it, and start the next step without waiting for a reply, whatever the stage's own file recommends at its end. Post one line per stage to the user: what it produced and which stage starts next.

After each step, apply the signals the stages raised. Write the line in use to `{scratch}/line.json` (the expanded line for a `from` line) and run `$SKILL_DIR/scripts/apply-signals.py` on the card and that file, with `--done` set to the number of steps run: `python3 "$SKILL_DIR/scripts/apply-signals.py" <card> {scratch}/line.json --done <steps run>`. It reads `## Signals` on the card and applies the matching rows of `./references/signals.json` (through `./references/catalog.json`) to the steps not yet run, each change checked by `validate-line.py`. A row is the approval: ask no approval. For each entry in `"applied"`, post a line comment on the ticket (a `## Assembly line` heading, a sentence naming the signal, the stage that raised it, its evidence and the stage added or removed, then the changed line's JSON in `stages` form), log a `line: signal` entry, `line: signal <signal> <raisedBy> -> <change> <stage> (<comment link>)`, to `## Decisions`, and run the rest from the report's `"line"`. When the run took its line from the line file, rewrite the line file with the changed line in `stages` form instead of posting a comment, and log its path in place of the comment link. For each entry in `"rejected"`, log `line: signal <signal> <raisedBy> rejected: <stage> <rule>` for each of its errors and keep the line. A resume reads the line file when it exists, else the line comment created last.

### Run log

Note `startedAt` before each stage starts and `endedAt` when it returns, both UTC ISO 8601 from `date -u +%Y-%m-%dT%H:%M:%SZ`. After every stage run, append one line to the file `assembly-line.runLog` names, before applying signals. Go-back reruns and each parallel branch count as a stage run. The script is `$SKILL_DIR/scripts/run-log.py`, where `$SKILL_DIR` is this skill's folder; it does not read the settings file.

```bash
python3 "$SKILL_DIR/scripts/run-log.py" append --log <assembly-line.runLog> --ticket <id> --kind <kind> --line <from> --stage <stage> --started-at <iso> --ended-at <iso> --verdict <verdict> --loops <n> --tokens <n> --changed-by <signal>
```

- `--log` is the value of `assembly-line.runLog`; leave it out for the default.
- `--kind` is the `kind` from section 1 and `--line` the name the line comment starts `from`; leave a flag out when its value is `null`, and the record holds `null`.
- `--line` is `null` for a line written out in `stages`.
- `--loops` (`loops`) is how many times this stage already ran earlier in this run of the line: `0` on its first run, one more for each go-back rerun.
- `--tokens` (`tokens`) is the total the harness reports for the stage's sub-agent. Leave it out, so it is `null`, when there is none, and always for `judge`, `ui-review`, `security-review` and `review-fix`, which run in this session.
- `--changed-by` (`changedBy`) is the signal name from an `apply-signals.py` `"applied"` add entry for that stage; leave it out, so it is `null`, otherwise.
- `--verdict` is the stage's `Verdict:`; a stage that stops without one logs its `runStatus` (`blocked`, `needs-input`, `gate`).
- A parallel group logs one line per branch stage, each with its own times.

A failed append (exit 1 or 2) is logged to `## Decisions` as `line: run-log failed <stage>: <error>`, and the run goes on: the run log never stops the run.

### Line board

After each step, after the run log append, run the board. The script is `$SKILL_DIR/scripts/board.py`, where `$SKILL_DIR` is this skill's folder; it does not read the settings file and writes nothing.

```bash
python3 "$SKILL_DIR/scripts/board.py" --cards <feature-recipe.cardsDir> --log <assembly-line.runLog>
```

- `--cards` is the value of `feature-recipe.cardsDir` and `--log` the value of `assembly-line.runLog`; leave a flag out for its default.
- It prints a ticket table of every running card, a stage table with how many wait at each stage, and a `Bottleneck:` line.
- When the ticket table lists more than one ticket, that step's one-line report to the user names the command.
- A failed board (exit 1 or 2) is logged to `## Decisions` as `line: board failed: <error>`, and the run goes on: the board never stops the run.

## 6. Stop conditions

Stop only at the line's end (`runStatus: terminal`), at a gate (`runStatus: gate`), or when a stage reports `blocked` or `needs-input` in `runStatus`: a real one-way door or an ambiguity with no reasonable default; never merely because a stage finished. On a stop, report the open question to the user directly in this chat, after section 7. Running this skill again on the same ticket resumes at the step after the last `line: step` line.

## 7. Close down

Run this section at every stop: the end, `blocked`, `needs-input` or a gate,
before the report in chat. Nothing this line started outlives the run.

While the run goes on, a sub-agent or background shell whose output has not
grown for 30 minutes is stalled, such as a shell stuck on a command that never
returns. Stop it with `TaskStop`, log `line: stalled <id> <last command>` to
`## Decisions`, and start its stage again once. A second stall on the same
stage stops the run with `runStatus: blocked`, and this section runs.

1. **Sub-agents.** Each sub-agent this line started has returned, or gets
   stopped: in Claude Code, `TaskStop` on its id; elsewhere, the runtime's own
   way.
2. **Background shells.** Stop each background shell this line started, a dev
   server or watcher brought up for screenshots included: in Claude Code,
   `TaskStop` on the shell's id.
3. **Processes.** A process still running on a port or pid this line noted gets
   stopped by that port or pid. Leave alone any process this line did not start.
4. **Log.** Log `line: closed down <n> agents, <n> shells` to
   `## Decisions`. Anything that would not stop goes on that line with its id,
   and into the chat report.
