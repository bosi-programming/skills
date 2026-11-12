---
name: recipe-relay
description: Run feature-recipe phase by phase through isolated sub-agents, auto-taking every checkpoint's own stated recommendation instead of asking, moving from one unit to the next without pausing, and ending with a headless better-code-review pass whose findings it fixes. Use when the user wants the feature recipe run hands-off but supervised in the current session, without a cron job and without every design decision landing back in chat.
---

# Recipe Relay

Runs `../feature-recipe/` without changing any of its files. This
session stays live and orchestrates; each phase's actual work happens in an
isolated sub-agent told to auto-take every checkpoint's own recommendation,
so what reaches this chat is a one-line note per unit, not a design question.

The settings file's `## recipe-relay` section, read as
`../setup/references/config.md` says, holds rules for the project at hand.
Take it from the current folder's file, or from `$HOME`'s when the current
folder has none. Paste it word for word under a `Project rules:` line at the
end of every sub-agent prompt this skill writes, the review in section 5
included. A rule there beats a phase file's default, never a stop condition
in section 4. No section means no rules.

## 1. Start or resume

Read and follow `../feature-recipe/phases/phase-0-start.md` directly in
this session — not through a sub-agent. It's pure routing, and this session
needs the card's state to orchestrate anyway. Follow it as an interactive
invocation: take the task from what the user already said in this
conversation, and don't write `runMode: headless` to the card. A person is
running this, just not being asked every checkpoint. To route, this session
reads only the card's frontmatter; the units read the rest.

## 2. Run one unit per sub-agent

Determine the next unit from the card's `phase` / `runNext`:

- **Design unit.** `evaluate-ticket` (`../evaluate-ticket/SKILL.md`) and
  `plan-code` (`../plan-code/SKILL.md`) run as one unit, from whichever
  `runNext` names, so `plan-code` keeps what `evaluate-ticket` learned about
  the code. A `runNext` of the old `phase-1-reading-the-recipe.md` means
  `evaluate-ticket`; of the old `phase-2-mise-en-place.md`, `plan-code`. It
  ends with `plan-code`'s `## Interfaces` step, as step 1 of _Cooking in
  parallel_ says.
- `test` (`../test/SKILL.md`) and `code` (`../code/SKILL.md`) run as the
  units in _Cooking in parallel_ below, and the _UI review_ below follows its
  last unit. A `runNext` of `test`, `code`, or of the old `phase-3-cooking.md`
  or `phase-4-tasting.md` means these units.
- The Plating unit is `prepare-pr` (`../prepare-pr/SKILL.md`), which runs alone.
  A `runNext` of `prepare-pr` or of the old `phase-5-plating.md` means this
  unit. The Documentation unit is `code-docs` (`../code-docs/SKILL.md`), which
  runs alone too; a `runNext` of `code-docs` or of the old
  `phase-6-documentation.md` means it. Both run on the model
  `recipe-relay.routineModel` names, read from the settings file as
  `../setup/references/config.md` says. Its default, `''`, keeps the model this
  session runs on.

Spawn one `general-purpose` sub-agent per unit (full tool access — Cooking
and Plating need to write code, run tests, and open PRs) with a prompt to
this effect:

> Load and execute `{phase file(s)}` against the recipe card at `{card
> path}`. Follow each phase's own `## Headless` section for every checkpoint
> it names — grilling, section drafts, cross-checks, test-case lists,
> approvals, PR descriptions — taking the recommendation it states, and
> logging it to `## Decisions` prefixed `relay:` instead of `unattended:` (a
> person is running this, just not being asked).
> Do not read `../feature-recipe/references/headless.md`, though that section
> says to: this prompt holds what you need from it. Ignore that section's
> instructions about chaining past this unit's last phase file: stop and
> return control once its closing section (frontmatter update, one line to
> `## Decisions`) is written. Do not set `runMode` on the card. Never merge,
> delete work written on purpose, force-push, rewrite history, run an
> irreversible migration, or change credentials or production. At one of
> those, or at a question with no reasonable default, stop: write an entry to
> `## Open Questions` with an id, the question, the options and your
> recommendation; set `runStatus` to `needs-input` for a one-way door or
> `blocked` when something external must change; set `runQuestion` to the id;
> leave `runNext`, `phase` and `phasesCompleted` alone; and log the stop to
> `## Decisions`. Return at most 100 words on what got decided. The rest stays
> on the card.

For the Plating unit, add this to that prompt: open the PR ready for review,
never as a draft, and leave it that way. This overrides Plating's draft rule
for deferred CI checks and its Headless rule that opens drafts and never
promotes them. CI still gets waited on and fixed as Plating's section 5 says.
Skip Plating's section 2: section 5 below reviews the diff right after this
unit. Tell it also to move the task, in the tracker the card came from, to
`recipe-relay.reviewState`, default `In Review`, once the PR is open; an empty
value skips the move.

For the Documentation unit, add this to that prompt: when the task came from a
tracker, move it to `recipe-relay.doneState`, default `Done`; an empty value
skips the move. Both are read from the settings file as
`../setup/references/config.md` says.

### Cooking in parallel

Cooking splits so that tests and code get written at the same time, by
agents that cannot shape one to the other. Run the units below in order,
every time Cooking comes up, even when the task touches one repo. Run each
test writer, code writer and fix agent on the model
`recipe-relay.codingModel` names, read from the settings file as
`../setup/references/config.md` says. Its default, `''`, keeps the model this
session runs on.

1. **Interfaces.** Section 4 of `plan-code` writes `## Interfaces` to the card
   before either writer starts: for each repo the plan touches, the public
   names, their signatures and the files they live in. Both writers code to
   that section and nothing else. A plan too vague to name them stops the run
   with `runStatus: needs-input`, as section 4 says. A card resumed at Cooking
   with no such section gets one sub-agent that runs that section of
   `plan-code`.
2. **Writers.** For each repo, spawn its test writer and its code writer at
   the same time, both on the same branch and worktree the code runs from: the
   repo's own checkout, on `{branch}`, the branch the repo is on. Start every
   pair before waiting on any of them. Each writer commits only the files it
   wrote, with `git commit -- <paths>`, which leaves out anything the other writer
   has staged, and retries a commit that hits `index.lock`.
   - The **test writer** loads `test` (`../test/SKILL.md`) with the section 2
     prompt, limited to its repo. It reads the Acceptance Criteria, Testing
     Strategy, `## TDD Test Mapping` and `## Interfaces`, and never sees the
     code: it opens no file the code writer touches. It writes the tests for
     its repo, runs them, and confirms they fail; an import error for a name
     that does not exist yet counts as a fail. It commits and marks each case
     written in `## TDD Test Mapping`. A test that already passes gets logged
     to `## Decisions` as `relay:`, with its name; the writer leaves it in and
     carry on. It stops after `test`'s section 3 and does not load `code`.
   - The **code writer** loads `code` (`../code/SKILL.md`) with the section 2
     prompt, limited to its repo, and runs it as its _Beside test_ section
     says. It reads the Solution, Implementation Plan, Config changes and
     `## Interfaces`, and never sees the tests: it opens no test file. It
     writes the code for its repo and commits, without adding tests, holding
     to `code`'s standards and plan-drift rules, minus the step that runs the
     tests.
3. **Fix and taste.** Once both writers of every repo return, one sub-agent
   loads `code` (`../code/SKILL.md`) again, as the section 2 prompt says,
   with the tests and code already in place on `{branch}`. It starts at
   step 3 of `code`'s section 2: run the tests, make the red ones pass by
   fixing the code, not the test, unless the test contradicts `## Interfaces`
   or the Acceptance Criteria. Then it runs the rest of `code`. Tell it to
   skip `code`'s section 5: section 5 below runs the one review, right after
   Plating. With no review to lean on, `code` runs every project check
   itself, and those checks stay its hard gate.

### UI review

A UI review compares what the change renders with the design the task
carries. It runs only when the card's Solution changes a surface a person sees
in the browser; for any other change, skip this section and log the skip to
`## Decisions` as `relay:`.

1. **Order.** Start the UI review after the fix and taste agent returns from
   step 3 of _Cooking in parallel_.
2. **Screenshots.** Tell the fix and taste agent, in its prompt, to do this
   once `code`'s checks pass. It clears the folder `{scratch}/ui-review/`,
   brings the change up the way the project already does, and screenshots every
   state of the changed surface the Acceptance Criteria name into that folder.
   Once the screenshots are saved, it stops what it brought up.
   When it cannot bring the surface up, its summary says `none: <reason>`: the
   verdict is `inconclusive`, and no reviewer starts.
3. **Review.** Load, read completely and execute `../ui-review/SKILL.md` on
   the card, handing it the project rules above.
4. **Route the result.** A `fail` verdict goes back to the fix agent, with the
   screenshots' paths, in a new fix and taste round followed by a new review;
   do this at most twice. A third `fail` stops the run with
   `runStatus: needs-input`, as section 4 says. An `inconclusive` verdict goes
   on the card with its reason, logged as `relay:`, and the run moves on to
   Plating.

## 3. Move to the next unit

When a sub-agent returns, start the next unit's sub-agent straight away,
whatever its phase file recommends at Phase done. New session and Continue
mean the same here: each unit already runs in a clean sub-agent. Post one line
per unit to the user — what it produced and which phase starts next — without
waiting for a reply. After `prepare-pr` returns with a PR open, the next
unit is section 5, run before `code-docs` starts. `code-docs` then
runs as usual, unless `prepare-pr` stopped on a chunk still pending.

## 4. Stop conditions

Same as feature-recipe's own contract: stop only when `code-docs` has returned
and section 5 is done, or a sub-agent reports `runStatus: blocked` / `needs-input` — a
real one-way door or an ambiguity with no reasonable default — never merely
because a unit finished. On a stop, report the open question to the user
directly in this chat, after section 6. Resuming the conversation with an answer and
re-invoking this skill picks the card back up through Phase 0's own resume
logic.

## 5. Review and fix

When `prepare-pr` returns with a PR open, the branch holds the code.
Start this section at once, whatever the card's `status` or `runStatus`, and
with a chunked delivery, for each chunk's PR as it opens. Do not wait for
`code-docs` or for `runStatus: terminal`. If the run stopped on `blocked` /
`needs-input` instead, skip this section.

Load, read completely and execute `../review-fix/SKILL.md` on the card, handing it the project rules above.

## 6. Close down

Run this section at every stop: the end, `blocked`, `needs-input` or a gate,
before the report in chat. Nothing this run started outlives the run.

While the run goes on, a sub-agent or background shell whose output has not
grown for 30 minutes is stalled, such as a shell stuck on a command that never
returns. Stop it with `TaskStop`, log `relay: stalled <id> <last command>` to
`## Decisions`, and start its unit again once. A second stall on the same
unit stops the run with `runStatus: blocked`, and this section runs.

1. **Sub-agents.** Each sub-agent this run started has returned, or gets
   stopped: in Claude Code, `TaskStop` on its id; elsewhere, the runtime's own
   way.
2. **Background shells.** Stop each background shell this run started, a dev
   server or watcher brought up for screenshots included: in Claude Code,
   `TaskStop` on the shell's id.
3. **Processes.** A process still running on a port or pid this run noted gets
   stopped by that port or pid. Leave alone any process this run did not start.
4. **Log.** Log `relay: closed down <n> agents, <n> shells` to
   `## Decisions`. Anything that would not stop goes on that line with its id,
   and into the chat report.
