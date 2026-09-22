---
name: bosi-feature-recipe
description: Take a task from a rough idea to a merged PR, cooked in six named phases — Reading the Recipe, Mise en Place, Cooking, Tasting, Plating, Documentation — each one able to end in a clean context, except Reading the Recipe and Cooking/Tasting, which default to continuing straight into the next phase. Use when the user says "run the recipe", "cook this ticket", "cook this task", or "feature recipe".
---

A feature delivered the way a dish gets cooked: read the recipe before you touch anything, get every ingredient ready, cook, taste before it leaves the kitchen, plate it, then write down what you made. Six phases, most defaulting to a fresh context between them — Reading the Recipe and Cooking/Tasting continue straight through instead — held together by one artifact that survives the reset either way: the **recipe card**, a markdown file at `./recipes/{task-slug}.md` in the current project.

This skill carries no opinion about which issue tracker, chat tool, or docs system the project uses. It speaks in outcomes — "record this somewhere your team can see it", "get this in front of reviewers" — and leans on whatever tools are already available in the session to make that outcome real. Where nothing is available, it asks or skips.

Load, read completely, then execute `./phases/phase-0-start.md` to begin.

## Headless runs

Phases 1 to 6 can run with no human in the loop — a night run. Start one with
`--headless` at whatever step the card is on, even a bare task with no card
yet, and it carries the work through Reading the Recipe, Mise en Place,
Cooking, Tasting, Plating and Documentation in one turn, taking the
recommendation at each checkpoint and recording it as `unattended:`, so the
morning can see what was decided while nobody was watching. It stops only when
the recipe is finished or something needs a person — never at a phase boundary,
and never to open a one-way door: no non-draft PR, no merge, no deleted work.
The mode is recorded on the card, so a run resumed in a fresh context still
knows not to wait on anyone, and so is the run's result — `runStatus`,
`runNext` and `runQuestion` in the frontmatter, never only in what the run
printed. Only Phase 0 stays purely mechanical either way — there's nothing in
it worth a recommendation. The full contract is `./references/headless.md`;
read it before running or answering a headless run.

## Rules for all phases

- Never, ever, comment a code unless the package.json, README.md, AGENTS.md or CLAUDE.md explicit tell the code is an external facing package. If that is the case, only document external facing code with the language specific docs comment, like TSDocs for TS.
