---
name: recipe-relay
description: Run bosi-feature-recipe phase by phase through isolated sub-agents, auto-taking every checkpoint's own stated recommendation instead of asking, while this session still gets a visible checkpoint at the phase boundaries bosi-feature-recipe itself flags as significant. Use when the user wants the feature recipe run hands-off but supervised in the current session, without a cron job and without every design decision landing back in chat.
---

# Recipe Relay

Runs `../bosi-feature-recipe/` without changing any of its files. This
session stays live and orchestrates; each phase's actual work happens in an
isolated sub-agent told to auto-take every checkpoint's own recommendation,
so the only thing that reaches this chat is a phase-boundary checkpoint, not
a design question.

## 1. Start or resume

Read and follow `../bosi-feature-recipe/phases/phase-0-start.md` directly in
this session — not through a sub-agent. It's pure routing, and this session
needs the card's state to orchestrate anyway. Follow it as an interactive
invocation: take the task from what the user already said in this
conversation, and don't write `runMode: headless` to the card. A person is
running this, just not being asked every checkpoint.

## 2. Run one unit per sub-agent

Determine the next unit from the card's `phase` / `runNext`:

- `phase-3-cooking.md` + `phase-4-tasting.md` are one unit — bosi-feature-recipe
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
> short summary — what got decided — plus this unit's own stated Phase-done
> recommendation (New session or Continue), quoted from its own text.

## 3. Checkpoint between units

Read the sub-agent's returned recommendation as that phase's own file states
it, not decided by this skill:

- **New session (recommended)** — post a short visible checkpoint to the
  user: what the unit produced, in one or two lines, and which phase starts
  next. Give them a beat to interject before continuing.
- **Continue**, or no menu at all (Cooking/Tasting) — no checkpoint; start
  the next unit's sub-agent straight away.

## 4. Stop conditions

Same as bosi-feature-recipe's own contract: stop only when the card reaches
`terminal`, or a sub-agent reports `runStatus: blocked` / `needs-input` — a
real one-way door or an ambiguity with no reasonable default — never merely
because a unit finished. On a stop, report the open question to the user
directly in this chat. Resuming the conversation with an answer and
re-invoking this skill picks the card back up through Phase 0's own resume
logic.
