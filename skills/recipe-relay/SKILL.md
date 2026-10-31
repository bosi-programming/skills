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

- **Design unit.** `phase-1-reading-the-recipe.md` and
  `phase-2-mise-en-place.md` run as one unit, from whichever `runNext` names,
  so Mise en Place keeps what Reading the Recipe learned about the code. It
  ends by writing `## Interfaces`, as step 1 of _Cooking in parallel_ says.
- `phase-3-cooking.md` + `phase-4-tasting.md` run as the units in _Cooking in
  parallel_ below, and the _UI review_ below follows its last unit.
- `phase-5-plating.md` and `phase-6-documentation.md` each run alone, on the
  model `recipe-relay.routineModel` names, read from the settings file as
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

1. **Interfaces.** The design unit's last step reads the card's Solution,
   Implementation Plan and `## TDD Test Mapping`, and writes a `## Interfaces`
   section to the card before either writer starts. For each repo the plan
   touches, it lists the public names, their signatures and the files they
   live in. Both writers code to that section and nothing else. A plan too
   vague to name them stops the run with `runStatus: needs-input`, as section 4
   says. A card resumed at Cooking with no such section gets one sub-agent that
   writes it.
2. **Writers.** For each repo, spawn its test writer and its code writer at
   the same time, both on the same branch and worktree the code runs from: the
   repo's own checkout, on `{branch}`, the branch the repo is on. Start every
   pair before waiting on any of them. Each writer stages and commits only the
   files it wrote, by path, and retries a commit that hits `index.lock`.
   - The **test writer** reads the Acceptance Criteria, Testing Strategy,
     `## TDD Test Mapping` and `## Interfaces`, and never sees the code: it
     opens no file the code writer touches. It writes the tests for its repo,
     runs them, and confirms they fail; an import error for a name that does
     not exist yet counts as a fail. It commits and marks each case written in
     `## TDD Test Mapping`. A test that already passes gets logged to
     `## Decisions` as `relay:`, with its name; the writer leaves it in and
     carry on.
   - The **code writer** reads the Solution, Implementation Plan, Config
     changes and `## Interfaces`, and never sees the tests: it opens no test
     file. It writes the code for its repo and commits, without adding tests.
     It follows section 1 of `phase-3-cooking.md` for standards and plan
     drift, minus the test steps.
3. **Fix and taste.** Once both writers of every repo return, one sub-agent
   loads `phase-3-cooking.md` and `phase-4-tasting.md`, as the section 2
   prompt says, with the tests and code already in place on `{branch}`. It
   starts at step 4 of Cooking's section 1: run the tests, make the red ones
   pass by fixing the code, not the test, unless the test contradicts
   `## Interfaces` or the Acceptance Criteria. Then it runs the rest of
   Cooking and all of Tasting. Tell it to skip Tasting's section 1: section 5
   below runs the one review, right after Plating. With no review to lean on,
   Tasting runs every project check itself, and those checks stay its hard
   gate.

### UI review

A UI review compares what the change renders with the design the task
carries. It runs only when the card's Solution changes a surface a person sees
in the browser; for any other change, skip this section and log the skip to
`## Decisions` as `relay:`.

1. **Order.** Start the UI reviewer after the fix and taste agent returns from
   step 3 of _Cooking in parallel_. Run the reviewer on the model
   `recipe-relay.uiReviewerModel` names, read from the settings file as
   `../setup/references/config.md` says. Its default, `''`, keeps the model
   this session runs on. The reviewer never starts the app and takes no
   screenshots: it judges the ones the fix and taste agent captures.
2. **Screenshots.** Tell the fix and taste agent, in its prompt, to do this
   once Tasting's checks pass. It clears the folder `{scratch}/ui-review/`,
   brings the change up the way the project already does, and screenshots every
   state of the changed surface the Acceptance Criteria name into that folder.
   When it cannot bring the surface up, its summary says `none: <reason>`: the
   verdict is `inconclusive`, and no reviewer starts.
3. **The design.** The design is the image attached to the task, read with
   whatever tool the session has for the tracker. A design-tool frame the task
   links may settle a region the image leaves unclear, but never stands in
   for a missing image. No design at all makes the verdict `inconclusive`.
   The reviewer never guesses the design from the task's text.
4. **The comparison.** Walk the design top to bottom and name, for each
   difference, the design region and the screenshot it comes from. Rate it:
   critical when the changed surface is missing, blank or broken; major for a
   wrong component or structure, a missing or extra field, wrong content or
   order, or a state the design shows that the build lacks; minor for small
   spacing, colour or weight drift and anything the image cannot settle.
   Judge what a person sees, not the code. Write the verdict and the findings
   to a `## UI Review` section on the card.
5. **Route the result.** Critical and major findings go back to the fix
   agent, with the screenshots' paths, in a new fix and taste round followed by
   a new review; do this at most twice. A third round with critical or
   major findings stops the run with `runStatus: needs-input`, as section 4
   says. Minor findings never send work back: log them to
   `## Quality Gate Results`. An `inconclusive` verdict goes on the card with
   its reason, logged as `relay:`, and the run moves on to Plating.

## 3. Move to the next unit

When a sub-agent returns, start the next unit's sub-agent straight away,
whatever its phase file recommends at Phase done. New session and Continue
mean the same here: each unit already runs in a clean sub-agent. Post one line
per unit to the user — what it produced and which phase starts next — without
waiting for a reply. After `phase-5-plating.md` returns with a PR open, the next
unit is section 5, run before `phase-6-documentation.md` starts. Phase 6 then
runs as usual, unless Plating stopped on a chunk still pending.

## 4. Stop conditions

Same as feature-recipe's own contract: stop only when Phase 6 has returned
and section 5 is done, or a sub-agent reports `runStatus: blocked` / `needs-input` — a
real one-way door or an ambiguity with no reasonable default — never merely
because a unit finished. On a stop, report the open question to the user
directly in this chat. Resuming the conversation with an answer and
re-invoking this skill picks the card back up through Phase 0's own resume
logic.

## 5. Review and fix

When `phase-5-plating.md` returns with a PR open, the branch holds the code.
Start this section at once, whatever the card's `status` or `runStatus`, and
with a chunked delivery, for each chunk's PR as it opens. Do not wait for
Phase 6 or for `runStatus: terminal`. If the run stopped on `blocked` /
`needs-input` instead, skip this section.

1. Spawn one `general-purpose` sub-agent on `recipe-relay.routineModel` to run
   `../better-code-review/SKILL.md` with `--headless`. The fixed point is the
   merge base of the work branch and the default branch; if the recipe worked
   on the default branch itself, it is the commit before the recipe's first
   one. The spec source is the task on the card. Have it write the review's
   output as it stands to `{scratch}/review.txt` and return only its `Totals:`
   line.
2. Spawn one sub-agent on `recipe-relay.codingModel` to work through the
   findings in that file, on the same branch, by their `Verified:` tag. A `ran`
   finding is proved: go to the fix. A `read` finding gets read at its
   `file:line` first. A `no` finding: verify it first, by running or reading
   what it names, and reject it if it does not hold. Log each `judgement call`
   and `scope creep` finding to `## Quality Gate Results` and leave the code as
   it is; deleting work written on purpose is a one-way door. Write a failing
   test first where the finding is a behaviour, then fix, then run the
   project's scoped tests and lint. Push to the open PR, which stays ready for
   review. Log each finding you reject to `## Decisions` as `relay:`, with the
   reason, instead of changing the code. Log the review's `Reviewed:` line and
   each `Not verified:` entry there too, so the gap stays on the card. Return at
   most 150 words: what got fixed, what got rejected and why, what stays not
   verified.
3. Tell the user, in short bullets, which findings were fixed and which were
   rejected, with the reason, and what the review left not verified.
