---
name: recipe-relay
description: Run feature-recipe phase by phase through isolated sub-agents, auto-taking every checkpoint's own stated recommendation instead of asking, moving from one unit to the next without pausing, and ending with a headless better-code-review pass whose findings it fixes. Use when the user wants the feature recipe run hands-off but supervised in the current session, without a cron job and without every design decision landing back in chat.
---

# Recipe Relay

Runs `../feature-recipe/` without changing any of its files. This
session stays live and orchestrates; each phase's actual work happens in an
isolated sub-agent told to auto-take every checkpoint's own recommendation,
so what reaches this chat is a one-line note per unit, not a design question.

## 1. Start or resume

Read and follow `../feature-recipe/phases/phase-0-start.md` directly in
this session — not through a sub-agent. It's pure routing, and this session
needs the card's state to orchestrate anyway. Follow it as an interactive
invocation: take the task from what the user already said in this
conversation, and don't write `runMode: headless` to the card. A person is
running this, just not being asked every checkpoint.

## 2. Run one unit per sub-agent

Determine the next unit from the card's `phase` / `runNext`:

- `phase-3-cooking.md` + `phase-4-tasting.md` are one unit — feature-recipe
  already runs them back-to-back with no menu, in either of its own modes.
- Every other phase (`phase-1-reading-the-recipe.md`, `phase-2-mise-en-place.md`,
  `phase-5-plating.md`, `phase-6-documentation.md`) is its own unit.

Spawn one `general-purpose` sub-agent per unit (full tool access — Cooking
and Plating need to write code, run tests, and open PRs) with a prompt to
this effect:

> Load and execute `{phase file(s)}` against the recipe card at `{card
> path}`. Follow that phase's own `## Headless` section for every checkpoint
> it names — grilling, section drafts, cross-checks, test-case lists,
> approvals, PR descriptions — taking the recommendation it states, and
> logging it to `## Decisions` prefixed `relay:` instead of `unattended:` (a
> person is running this, just not being asked). Ignore that section's
> instructions about chaining into the next phase file: stop and return
> control once this unit's own closing section (frontmatter update, one line
> to `## Decisions`) is written. Do not set `runMode` on the card. Return a
> short summary of what got decided.

## 3. Move to the next unit

When a sub-agent returns, start the next unit's sub-agent straight away,
whatever its phase file recommends at Phase done. New session and Continue
mean the same here: each unit already runs in a clean sub-agent. Post one line
per unit to the user — what it produced and which phase starts next — without
waiting for a reply.

## 4. Stop conditions

Same as feature-recipe's own contract: stop only when the card reaches
`terminal` and section 5 is done, or a sub-agent reports `runStatus: blocked` / `needs-input` — a
real one-way door or an ambiguity with no reasonable default — never merely
because a unit finished. On a stop, report the open question to the user
directly in this chat. Resuming the conversation with an answer and
re-invoking this skill picks the card back up through Phase 0's own resume
logic.

## 5. Review and fix

When the card reaches `terminal`, the branch holds the code. If the run
stopped on `blocked` / `needs-input` instead, skip this section.

1. Spawn one `general-purpose` sub-agent to run `../better-code-review/SKILL.md`
   with `--headless`. The fixed point is the merge base of the work branch and
   the default branch; if the recipe worked on the default branch itself, it
   is the commit before the recipe's first one. The spec source is the task on
   the card. Have it return the review's output as it stands.
2. Work through the findings in this session, on the same branch, by their
   `Verified:` tag. A `ran` finding is proved: go to the fix. A `read` finding
   gets read at its `file:line` first. A `no` finding: verify it first, by
   running or reading what it names, and reject it if it does not hold. Write
   a failing test first where the finding is a behaviour, then fix, then run
   the project's scoped tests and lint. Push to the open PR and leave it in
   the state Plating left it. Log each finding you reject to `## Decisions` as
   `relay:`, with the reason, instead of changing the code. Log the review's
   `Reviewed:` line and each `Not verified:` entry there too, so the gap stays
   on the card.
3. Tell the user, in short bullets, which findings you fixed and which you
   rejected, with the reason, and what the review left not verified.
