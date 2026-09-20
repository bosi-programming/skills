---
name: bosi-feature-recipe
description: Take a task from a rough idea to a merged PR, cooked in six named phases — Reading the Recipe, Mise en Place, Cooking, Tasting, Plating, Documentation — each one ending in a clean context. Use when the user says "run the recipe", "cook this ticket", "cook this task", or "feature recipe".
disable-model-invocation: true
---

A feature delivered the way a dish gets cooked: read the recipe before you touch anything, get every ingredient ready, cook, taste before it leaves the kitchen, plate it, then write down what you made. Six phases, each one a fresh context by default, held together by one artifact that survives the reset between them — the **recipe card**, a markdown file at `./recipes/{task-slug}.md` in the current project.

This skill carries no opinion about which issue tracker, chat tool, or docs system the project uses. It speaks in outcomes — "record this somewhere your team can see it", "get this in front of reviewers" — and leans on whatever tools are already available in the session to make that outcome real. Where nothing is available, it asks or skips.

Load, read completely, then execute `./phases/phase-0-start.md` to begin.

## Headless runs

Phases 3 to 6 can run with no human in the loop, driven by an external agent
that answers the checkpoints and routes the phases. Phases 0 to 2 cannot — the
grill round and the design approval are where intent enters the recipe. Start a
headless run with `--headless`; the mode is recorded on the card so a phase
resumed in a fresh context still knows not to wait on a person. Every headless
phase ends its turn with one routing line for the driver to follow, and never
opens a one-way door — no non-draft PR, no merge, no deleted work — without an
explicit answer. The full contract is `./references/headless.md`; read it
before running or answering a headless phase.

## Rules for all phases

- Never, ever, comment a code unless the package.json, README.md, AGENTS.md or CLAUDE.md explicit tell the code is an external facing package. If that is the case, only document external facing code with the language specific docs comment, like TSDocs for TS.
