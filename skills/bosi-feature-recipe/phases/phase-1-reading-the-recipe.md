# Phase 1 — Reading the Recipe

## Headless

A headless run does not belong here. If `runMode` is `headless` or the
invocation says `--headless`, stop: record the reason in `## Open Questions`
under a short id, and end the turn with
`RECIPE phase=reading-the-recipe status=blocked next=phase-1-reading-the-recipe.md card=<path> question=<id>`.
The grill round is where the user's intent enters the recipe, so a phase that
answered it for itself would be inventing requirements. See
`../references/headless.md`.

Understand the task and the code it lands on before anything gets designed.

## 1. Load the task

Read whatever the recipe card's `task` field points at. If it names something
a tool already in this session can fetch (an issue tracker link, a document),
fetch it and present the real title, description, and any acceptance
criteria already stated. Otherwise take the user's description as given.

## 2. Visualize the code as it stands today

The `code-visualizer` skill draws a diff, and there's no diff yet on a fresh task —
so point it at a stand-in: a recent commit range scoped to the paths the task
will likely touch (find them by searching the codebase for the area the task
describes, then take the last handful of commits that touched them).

Skip this and say why when the task is a genuinely new module or file with
no existing code to show the shape of — don't invoke the skill and lean on
its own empty-diff fallback.

## 3. Close every gap with `grill-me` secondary skill

Seed its design tree with the standard completeness dimensions for a task
like this one: the problem it solves, who benefits and how, what's in and
out of scope, testable acceptance criteria, edge cases and error scenarios,
and any external dependencies. Invoke the `grill-me` secondary skill that is on `../dependencies/grill-me.md` against that tree until its
frontier is empty — this replaces asking one or two clarifying questions at
a time; the round-based frontier questioning gets to the same place faster
and more completely.

## 4. Write the Problem section

Once the design tree is settled, write the `## Problem` section of the
recipe card: the problem statement, the acceptance criteria, edge cases, and
dependencies that came out of the grilling.

If the task came from a tracker with validated, agreed content, record that
validated version back there too — as an outcome ("update the ticket with
what we settled on"), not by naming a specific tool; use whatever's already
available in this session for that tracker.

Append one line to `## Decisions`: what was settled and why. Update the
frontmatter — `phase: 'reading-the-recipe'`, append to `phasesCompleted`,
`lastTouched`.

## 5. Phase done

> **Phase done. [N] New session (recommended) — resume next phase fresh. [C] Continue here.**

**N:** confirm the card is saved, tell the user to resume with the same
trigger phrase in a new session — Phase 0 will pick up here. End the session.

**C:** load, read completely, and execute `phase-2-mise-en-place.md`.
