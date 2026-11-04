---
name: feature-recipe
description: Take a task from a rough idea to a merged PR, cooked in six named stages — evaluate-ticket, plan-code, test, code, prepare-pr, code-docs — each one able to end in a clean context, except evaluate-ticket and test, which default to continuing straight into the next phase. Use when the user says "run the recipe", "cook this ticket", "cook this task", or "feature recipe".
---

A feature delivered the way a dish gets cooked: read the recipe before you touch anything, get every ingredient ready, cook, taste before it leaves the kitchen, plate it, then write down what you made. Six stages, most defaulting to a fresh context between them — the first and `test` continue straight through instead — held together by one artifact that survives the reset either way: the **recipe card**, a markdown file at `./recipes/{task-slug}.md` in the current project, or in whatever folder the settings file names. The settings file also picks the mode a run takes when the request names none; `../setup/references/config.md` describes it.

This skill carries no opinion about which issue tracker, chat tool, or docs system the project uses. It speaks in outcomes — "record this somewhere your team can see it", "get this in front of reviewers" — and leans on whatever tools are already available in the session to make that outcome real. Where nothing is available, it asks or skips.

Load, read completely, then execute `./phases/phase-0-start.md` to begin.

All six stages are skills of their own, `evaluate-ticket` (`../evaluate-ticket/SKILL.md`), `plan-code` (`../plan-code/SKILL.md`), `test` (`../test/SKILL.md`), `code` (`../code/SKILL.md`) `prepare-pr` (`../prepare-pr/SKILL.md`) and `code-docs` (`../code-docs/SKILL.md`): Phase 0 routes to them, `evaluate-ticket` hands on to `plan-code`, `plan-code` hands on to `test`, `test` hands on to `code`, `code` hands on to `prepare-pr`, and `prepare-pr` hands on to `code-docs`. Each also runs alone on a card.

## Headless runs

Phases 1 to 6 can run with no human in the loop — a night run. Start one with
`--headless`, or make it the default with `feature-recipe.defaultMode`, at
whatever step the card is on, even a bare task with no card
yet, and it carries the work through `evaluate-ticket`, `plan-code`,
`test`, `code`, `prepare-pr` and `code-docs` in one turn, taking the
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

- Never comment code. The one exception: when `package.json`, `README.md`, `AGENTS.md` or `CLAUDE.md` says the code is a package others consume, document its public surface, and only that, in the language's doc-comment format, such as TSDoc for TypeScript.
