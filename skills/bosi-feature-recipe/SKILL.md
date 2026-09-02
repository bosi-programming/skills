---
name: bosi-feature-recipe
description: Take a task from a rough idea to a merged PR, cooked in six named phases — Reading the Recipe, Mise en Place, Cooking, Tasting, Plating, Documentation — each one ending in a clean context. Use when the user says "run the recipe", "cook this ticket", "cook this task", or "feature recipe".
disable-model-invocation: true
---

A feature delivered the way a dish gets cooked: read the recipe before you touch anything, get every ingredient ready, cook, taste before it leaves the kitchen, plate it, then write down what you made. Six phases, each one a fresh context by default, held together by one artifact that survives the reset between them — the **recipe card**, a markdown file at `./recipes/{task-slug}.md` in the current project.

This skill carries no opinion about which issue tracker, chat tool, or docs system the project uses. It speaks in outcomes — "record this somewhere your team can see it", "get this in front of reviewers" — and leans on whatever tools are already available in the session to make that outcome real. Where nothing is available, it asks or skips.

Load, read completely, then execute `./phases/phase-0-start.md` to begin.
